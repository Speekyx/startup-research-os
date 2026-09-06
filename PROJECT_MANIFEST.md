# PROJECT MANIFEST — Startup Research OS

Version: 1.118
Status: Foundation
Owner: Speekyx (GitHub: `@Speekyx`)
Repository: startup-research-os
Last amended: 2026-09-06 (Sprint 1 / Mission 1.76)

---

# Version History

This manifest is amended in place with an explicit version bump and a changelog
entry. Git history plus this section provide the traceability that
`docs/CLAUDE.md` §Change control requires.

## 1.118 - 2026-09-06 (Sprint 1 / Mission 1.76)

**`NEXT_BOUNDED_EVIDENCE_MOVE_SELECTED`, candidate M1.** An audit and a prioritization, not
an acquisition: **0 records collected, 0 model calls, 0 embeddings, 0 canonical mutations**,
and the research state is identical before and after.

**MORE ROWS IS NOT MORE INFORMATION.** 58 Evidence rows are **10 proposition kinds** across
5 sources, and breadth is measured in kinds. The gate refuses a row count presented as a
dimension count, one kind counted twice, and a count of independent witnesses in a corpus
holding **zero** established independence groups.

**THE OPPORTUNITY'S FIRST BLOCKER WAS MIS-STATED, AND THE MISSION FOUND IT.** The record
says "no reviewed reliability applies, so this hypothesis can contribute to no score",
which reads as NOBODY HAS REVIEWED THIS. **A reviewed assessment already exists**, at 0.65
and 0.6, for exactly the measurement and purpose its six Wikimedia rows carry. It does not
apply for a different reason: **the Evidence cannot state its resource identity**, so the
repository's own `resolve_reliability` returns NO_APPLICABLE_ASSESSMENT with the detail
"this evidence record cannot state its measurement-and-purpose scope". Run against held
data, the same function **RESOLVES cleanly for TED**, whose claims carry `resource_id`, and
fails for Wikimedia and Stack Exchange, whose claims do not and whose acquisition lineage
has no such column at all. **The corpus is one deterministic binding away from its first
scorable evidence.**

**NO SCORE, NO WEIGHTS, NO PERCENTAGES.** The priority is an ordinal tier and a
lexicographic order fixed before the candidates were read. **TIER 2 IS EMPTY AND THAT
EMPTINESS IS THE FINDING**: no candidate both adds a currently absent decision-relevant
dimension AND is executable now. The one that would add a dimension needs a governance
review, a collector and a normalizer first.

**THE WINNER IS NOT UNIQUELY DOMINANT, AND THE RECORD SAYS SO.** Dominance is a **VETO**,
not the selection rule: a dominated candidate cannot win, and M1 is dominated by nothing.
The tier then decides. **Docker was not privileged for having an Opportunity row** -- the
two candidates attached to no Opportunity were ranked on their own terms and lost on
information gain, and the hypothesis was measured against every other subject holding
Evidence.

**TED IS SEPARATED, NOT COLLAPSED.** Its 12 rows establish MARKET_ACTIVITY -- that notices
were published whose reported values differ -- and **not** willingness to pay, actual spend,
a framework maximum or a buyer. Their subject relationship to the Docker hypothesis is
NOT_THE_SAME_SUBJECT, because cleaning and sanitation procurement is not the Docker subject
and looking commercially interesting is not a relation.

**THE REGISTERED-SOURCE GAP IS RECORDED, NOT FILLED.** No source reviewed under
`local-private-research-v1` reaches WILLINGNESS_TO_PAY, BUYER_OR_BUDGET_EXISTENCE for this
subject, SOLUTION_DISSATISFACTION or SOLUTION_GAP. The developer-ecosystem sources that
could speak to it have **no LOCAL review at all**, and under Mission 1.75's contract an
absent review is a refusal -- github's RESTRICTED state under the commercial profile says
nothing about LOCAL and was not borrowed. **No source was discovered and none was invented.**

**TWO CORRECTIONS THE GATE FORCED.** The score check first refused a field named
`why_no_score`, which is the record explaining that it issues none: **the word is not what
is dangerous, a NUMBER posing as a priority is**, so it now refuses a numeric value in a
scoring-shaped field. And ranking the gain classes by list position put UNKNOWN below
LOW_INCREMENTAL_GAIN -- but **UNKNOWN is an UNBOUNDED gain, not a small one**, and ordering
it below "a little" asserts exactly what UNKNOWN denies. It is excluded from the comparison
now, and a placement across it must name its criterion.

**Verification.** Probe of **46 deliberate violations, 46 caught, 0 escaped**, plus **3 of
3 positive controls**, six files restored byte for byte. All seventeen violation classes
are covered, several twice. **The controls are the point**: besides the committed state, a
TIE and a NO-ACTIONABLE-CANDIDATE outcome must both stay expressible, because a gate that
only accepts the answer we happened to reach is not a gate. **3083 bare-python tests**;
both runners green; `ruff format --check`, `ruff check` and mypy through `uv`; contract
generation `--check`; source catalog `--check`; all **49** CI gates, one of them new.

**Canonical state unchanged**: RawRecords 325, Normalized 325, Signals 33, Claims 44,
revisions 45, Evidence 58, INFERRED 1, thresholds 1, derivations 1, refusals 0,
ReliabilityAssessments 4, independence groups 0, Opportunities 1/1/7, Embeddings 0, sources
29, use profiles 2, migration head 0036. Globalping untouched at **11 PASS / 1 PARTIAL / 0
FAIL**, `COUNTERPART_UNRESOLVED`, recorded as a DEPENDENCY rather than a candidate and
**not checked externally**.

New: `docs/data/opportunity-evidence-breadth-audit-v1.json`,
`docs/data/evidence-completion-candidate-moves-v1.json`,
`docs/data/evidence-completion-priority-v1.json`, their three generated `.md` pages,
`infrastructure/scripts/render_evidence_breadth_priority.py` (CI gate 49),
`packages/inferred-claim-evaluator/python/tests/test_evidence_breadth_priority.py`, and
`docs/reports/mission-1.76-report.md`.

Changed: `docs/CLAUDE.md` 1.118 to 1.119; `.github/workflows/ci.yml` gains one gate.

Unchanged: every canonical research table, every source review, every Globalping record,
and the existing Opportunity.

## 1.117 - 2026-09-06 (Sprint 1 / Mission 1.75)

**`GATEWAY_USE_PROFILE_SCOPING_REPAIRED`.** The profile-blindness Mission 1.15.7 found and
Mission 1.17 grew is closed. Source governance reads require an explicit `use_profile`,
**there is no default**, and no fact crosses a profile boundary.

**THE DEFECT REACHED THREE ROUTES, NOT TWO.** The brief named `/sources` and the
eligibility route. `GET /sources/{id}` had the same unscoped join AND an unscoped review
lookup, which made it **the worst of the three**: it returns the review body and its
evidence URLs, so an arbitrary profile's row there does not merely mislabel a verdict, it
**hands back the documents behind an assessment the caller is not asking about**.

**THERE IS NO DEFAULT, AND THE REASON IS NOT CAUTION.** Both registered profiles are real
deployments reaching **different verdicts about the same sources**, so any default would
answer a question the caller did not ask and would look exactly like an answer. Local,
commercial, environment-selected, workspace-derived, first-available-review and
fall-back-to-the-other were each considered and each refused for its own reason. A missing
profile is 422; an unregistered one is 422; and **an absent review under the requested
profile is a refusal, never a reason to consult another profile** -- which is the contract
`registry.source_eligibility` states in its own COMMENT.

**THE FIX IS IN THE JOIN, NOT OVER IT.** The profile is a join predicate, so there is no
duplication to deduplicate. The join is LEFT: a source the requested profile has never
reviewed is **still listed**, marked unreviewed and ineligible, because hiding it would
make "not reviewed here" indistinguishable from "not registered". **8 duplicated sources
before, 0 after**, under every profile.

**`collector_enabled` IS PROFILE-RELATIVE TOO**, and that is new information. It is a
column on the SOURCE carrying its own `collector_use_profile`, and the trigger checks
eligibility under THAT profile. Served flat beside a scoped verdict it reads as "enabled
for you" -- `ted-eu` is enabled under local and listed under commercial, where it is not
eligible -- so the re-pointed tripwire's first form, **enabled implies eligible**, was
still asserting a property the database never had. The routes now return
`collector_use_profile` and `collector_enabled_for_requested_profile` beside the flag.

**A HARD-CODED DEFAULT WAS HIDING IN DEAD CODE.** `read_sources` wrote
`commercial-multi-tenant-research-v1` into its SQL; nothing called it, so nothing had
chosen that profile and **the first caller would have inherited an answer it never asked
for**. It takes an explicit profile now. **No caller's intended profile had to be guessed,
because no production HTTP caller exists.**

**ONE MIGRATION, EXPLAINED BEFORE IT WAS WRITTEN**, and it is a single `GRANT SELECT` with
no DDL. The runtime role could not read `registry.use_profiles`, the canonical vocabulary
-- the one table migration 0021 created and forgot to grant, unnoticed because nothing read
it at runtime. **The vocabulary cannot be resolved from what was already readable**:
`source_eligibility` and `assessed_use_profile` enumerate the profiles that have BEEN USED,
not those that are REGISTERED, so validating against them would refuse a registered profile
nobody has reviewed under yet -- the state every new profile begins in. No row is inserted,
updated or deleted; there is no historical-data consequence; and the runtime role still
cannot write anywhere in `registry`.

**THREE PLACES PINNED A MOVING FACT.** Applying 0036 broke two CI gates and one pytest
test that compared the LIVE migration head against a literal, asserting historical facts through a measurement of the
present -- so any later migration would have broken them. Each now asserts that the
migration it NAMES exists and that its own record still says what it said. **Being the
newest was never the property that made either record correct.**

**BOTH MISSION 1.17 TRIPWIRES WERE RE-POINTED, NOT DELETED.** The duplicate-set assertion
listed eight source ids and grew with every profile alignment; it is now RELATIONAL,
because **a test pinned to eight names would fail the next time the registry legitimately
grows, which is a test asserting that the project may never progress**. The conditions
assertion pinned `fred` at six, and the dangerous part was never the count: the six
collapsed to **three distinct condition_keys**, so a reader deduplicating by key would have
seen a plausible answer assembled from two profiles' facts.

**ALL TEN LEAKAGE CASES COVERED, FIVE OF THEM CONSTRUCTED.** The seeded registry gives
CASE A free and cannot give CASE B at all, and **skipping the direction the data happens
not to lean would have left the leak that direction could carry untested**. The fixtures
obey the rules they test around -- the registry refuses an approval with no evidence and a
condition satisfied by a bare boolean -- and purge BEFORE inserting, because a setup that
raises halfway leaves a row the next run then fails on for unrelated reasons.

**Verification.** Probe of **14 deliberate violations, 14 caught, 0 escaped**, plus **3 of
3 positive controls**, router restored byte for byte. **TWO ESCAPED ON THE FIRST RUN**, and
both were exactly the ones the brief warns about: resolving validity from reviews instead
of the vocabulary, and hard-coding the two profile names. Both pass against a suite that
only ever names the two live profiles, so closing them needed a fixture registering **a
third profile with no reviews** -- the only case that tells the three implementations
apart. **3029 bare-python tests**; both runners green; `ruff format --check`, `ruff check`
and mypy through `uv`; contract generation `--check`; all **48** CI gates.

**ZERO research mutation and zero external action.** RawRecords 325, Normalized 325,
Signals 33, Claims 44, revisions 45, Evidence 58, INFERRED 1, thresholds 1, derivations 1,
refusals 0, ReliabilityAssessments 4, independence groups 0, Opportunities 1/1/7,
Embeddings 0, registered sources 29, use_profiles 2 -- all unchanged. 0 research API calls,
0 provider contacts, 0 model calls, 0 embeddings, 0 scores. **Historical RawRecords were
not backfilled** and `build_raw_record` still writes `use_profile` on new ones: EXPLICIT
for new, NOT_ESTABLISHED_AND_NOT_BACKFILLED for historical. Globalping untouched: R1
`R1_PASS_PROVIDER_DECLARED_NO_REDIRECT`, R2 PARTIAL, **11 PASS / 1 PARTIAL / 0 FAIL**,
`COUNTERPART_UNRESOLVED`.

New: `infrastructure/db/migrations/0036_grant_use_profile_vocabulary.sql`,
`docs/data/use-profile-scoped-governance-read-v1.md`,
`services/gateway/python/tests/test_source_use_profile_scoping.py` (39 tests), and
`docs/reports/mission-1.75-report.md`.

Changed: `services/gateway/python/sros_gateway/api/sources.py` (all three routes);
`services/acquisition/python/sros_acquisition/registry/repositories.py` loses a hard-coded
profile; `services/gateway/python/tests/test_integration.py` re-points both tripwires;
`infrastructure/scripts/render_persistence_orchestration.py`,
`render_refusal_provenance_schema.py` and
`services/nlp/python/tests/test_refusal_provenance_schema.py` stop pinning the live
migration head -- **the third surfaced only because a background run's exit code was
checked rather than trusted**;
`docs/CLAUDE.md` 1.117 to 1.118.

Unchanged: every source review, every verdict, the eligibility view, the collector trigger,
`build_raw_record`, and every Globalping record.

## 1.116 - 2026-09-06 (Sprint 1 / Mission 1.74.7)

**`R1_CLOSED_PROVIDER_DECLARED_RIGHTS_SCOPE_REMAINS`.** An organisation member answered the
exact frozen GP-R1-Q1 question on the provider's own issue tracker. R1 moves to
`R1_PASS_PROVIDER_DECLARED_NO_REDIRECT`, C6 to `PASS`, the tally from 10/2/0 to **11 PASS /
1 PARTIAL / 0 FAIL** -- and **the counterpart is still not qualified.**

**THE REPLY IS FROZEN BEFORE IT IS READ.** The source record declares itself a source,
carries `contains_interpretation: false`, and holds no verdict and no evidence level; the
reasoning lives in a separate record that cites it **by hash and never restates its text**.
That split is not ceremony: **a single document holding both the evidence and the
conclusion can adjust the first to suit the second, and nothing in it would show the
adjustment.** The gate refuses the interpretation being written into the source, refuses
either restating the reply, and refuses either naming a digest the other does not hold.

**A SUPPLIED STRING IS A CLAIM.** The instruction quoted the reply; the stored comment
differs from that quotation by **one trailing space**. It changes no meaning, and that is
exactly why it is recorded -- **a record that adopted the quotation silently here would
have adopted it just as silently where it mattered.**

**BOTH HALVES, EXAMINED SEPARATELY.** The second clause is explicit. The first is
anaphoric, and read alone could denote the response after a redirect had been followed.
**The second clause forecloses that reading**: if the redirect is not followed there is no
post-redirect response for the phrase to denote, so the referent is FORCED rather than
chosen, and the reading does not depend on charity toward the answer. The review records
the weakness before recording why it does not survive.

**A SOLICITED ANSWER IS NOT A STATEMENT SOMEBODY FOUND.** Mission 1.74 refused to upgrade
on an incidental maintainer remark, and **that refusal is untouched**: the guard forbidding
any FOUND statement a closing level is byte-identical, and the answer lives in its own
block rather than being added to that list. The new level is defined by **five conditions
the gate checks one at a time** -- solicited, responsive to the exact predicate,
attributable, durable and citable, retrieved without a summarising extraction -- and
failing any one drops it back to the incidental level. Adding a closing level is the move
most open to motivated reasoning here, so the justification is **a condition written before
the answer existed**: Mission 1.74's own review recorded that R1 was closable by "one
documented sentence, **or one answer through the provider's technical channel**".

**DECLARED, NOT DOCUMENTED.** The frozen discriminator named
`R1_PASS_DOCUMENTED_NO_REDIRECT`; the verdict recorded is
`R1_PASS_PROVIDER_DECLARED_NO_REDIRECT`. The DECISION is honoured exactly and the LABEL is
narrowed, because the specification still contains **zero occurrences of 'redirect'** and
calling this DOCUMENTED would claim a surface that does not exist -- the gate now refuses
that verdict whenever no reviewed surface documents the behaviour. **What stays open at
PASS is written down**: the behaviour is declared and not specified, so a future change
would contradict no published document and this verdict would not detect it.

**THE TALLY MOVED AND THE VERDICT DID NOT.** Qualification needs all twelve mandatory
dimensions PASS and C9 is still PARTIAL on R2, so **a better tally is not a verdict**: 0
classes selected, 0 constructs, 0 independence groups, Q1 still not viable. **A closed
residual removes a reason not to proceed and supplies no reason to proceed.** Four records
were **superseded, never edited** -- the redirect review, the closure, the qualification
and the decision -- each gaining one appended forward pointer, and the gate asserts LIVE
that the predecessors still read 10/2/0, two residuals remaining and
`R1_PARTIAL_IMPLEMENTATION_ONLY`, **so an edit that backdated this closure into Mission
1.74 fails here.**

**TWO DEFECTS SURFACED BY THE FIRST LEGITIMATE TRANSITION.** **The R1 dispatch could never
have reached `BYTE_VERIFIED`**: Mission 1.74.1 defined the upgrade as a RAW READ of the
issue body and Mission 1.74.3's gate refused EVERY GitHub API call by this repository, so
the gate demanded a comparison and forbade the only mechanism that produces one. The
counter is split -- the WRITE half keeps the refusal at zero, and the READ half is not
merely permitted but **REQUIRED to be at least one whenever `raw_body_compared` is true**,
because a comparison with no read compared nothing. Value preserved, name and comparison
changed, exactly as in 1.74.3. With that resolved the read this mission needed anyway
performed the comparison: the posted body digest equals the `approved_body_sha256` recorded
**before** the post, the title matches character for character, and R1 reaches
`BYTE_VERIFIED`. **The paragraph break Mission 1.74.3 suspected was a conversion artifact
WAS one** -- it suspected correctly and refused the upgrade anyway, which is what made the
refusal worth anything. **The closure record asserted things that had become false**: its
gate pinned `enquiries_sent == 0`, no approval and no contact, constants from a mission
where nothing had been sent. They are now LIVE cross-checks against the dispatch records,
which is strictly stronger, and `provider_contacted` is true **for R1 only**, on a reply
that demonstrates receipt, with the gate refusing it overruling R2's own record.

**BOUNDED TO R1.** R2 was not examined, its dispatch state was not altered, no reply to it
is claimed, and **0 measurements, 0 target HTTP requests, 0 classes, 0 constructs, 0
independence groups, 0 canonical mutations, 0 Claims, 0 Evidence, 0 scores, 0 model calls,
0 migrations**. 4 public GitHub API reads, 0 writes, 0 comments created, 0 credential
reads. ONYPHE still `NOT_CHECKED_AFTER_DISPATCH`, Netlas still pending, ADR-039 untouched.

**Verification.** Gates probed with **95 deliberate violations, 95 caught** (92 by rule, 3
by drift), **0 escaped**, plus **4 of 4 positive controls**. **One escape was found and
closed**: deleting the solicited-answer block raised a bare `KeyError` rather than a
refusal, so the residuals gate now converts a missing field into a refusal the way the
dispatch gates already did. **The controls are the point**: a future documented sentence
must still close R1 the ORIGINAL way, and R1 must still be representable back at
`OPERATOR_ATTESTED` with no comparison -- a gate that only accepts the state we happen to
be in is not a gate. **One test mutates Mission 1.74's incidental statement specifically**,
because adding a closing level must not have widened the old guard. **3029 bare-python
tests**; both runners green; `ruff format --check`, `ruff check` and mypy all run through
`uv`; all **48** CI gates, **no new gate** -- the gates that govern these records already
existed and were extended.

New: `docs/data/globalping-r1-provider-reply-v1.json`,
`docs/data/globalping-r1-reply-review-v1.json`,
`docs/data/globalping-redirect-contract-review-v2.json`,
`docs/data/globalping-residual-closure-v2.json`,
`docs/data/globalping-counterpart-qualification-v3.json`,
`docs/data/quantity-class-selection-decision-v5.json`,
`packages/inferred-claim-evaluator/python/tests/test_r1_provider_reply.py`, and
`docs/architecture/mission-1.74.7-report.md`.

Changed: `infrastructure/scripts/render_globalping_residuals.py` gains the solicited-answer
checks, the supersession check and the missing-field conversion;
`infrastructure/scripts/render_r1_dispatch_approval.py` splits the API counter and gains
the byte-verification checks; `docs/data/globalping-r1-dispatch-approval-v1.json` reaches
`BYTE_VERIFIED`; the generated `mission-1.74-globalping-residuals-v1.md`,
`globalping-redirect-evidence-v1.md` and `mission-1.74.1-r1-dispatch-approval-v1.md`;
`packages/inferred-claim-evaluator/python/tests/test_globalping_residuals.py` and
`test_r1_dispatch_approval.py` re-pointed rather than deleted; `docs/CLAUDE.md` 1.116 to
1.117.

Unchanged, apart from one appended forward pointer each:
`globalping-redirect-contract-review-v1.json`, `globalping-residual-closure-v1.json`,
`globalping-counterpart-qualification-v2.json` and
`quantity-class-selection-decision-v4.json`. The R1 and R2 packets are byte-identical,
every R2 record is untouched, and no canonical table, source review or ADR was modified.

## 1.115 - 2026-09-06 (Sprint 1 / Mission 1.74.6)

**`R2_V2_DISPATCH_OPERATOR_ATTESTED_DELIVERY_UNCONFIRMED`.** The operator sent the approved
GP-R2-Q1 v2 email once, by hand, from `thib.chm@gmail.com` to `d@globalping.io`, and
attested to it. **No mailbox was read, no connector was used, and this repository sent
nothing.**

**A SEND IS NOT A DELIVERY.** This is the whole mission. A send is an act by the sender; a
delivery is an outcome at the receiver, and **the attestation establishes the first and is
silent on the second**. So `deliveries_confirmed` stays 0, the delivery status reads
`UNCONFIRMED`, and **`provider_contacted` stays FALSE** -- a contact means something
reached the provider, and only delivery would establish that. **This arc supplies its own
proof that the two come apart**: the v1 message to `legal@globalping.io` was sent too, and
then it bounced, and a record that had marked a contact at the moment of sending would
have been wrong within the hour. The distinction is now a RULE rather than a sentence:
`UNCONFIRMED` forbids a counted delivery and forbids a contact; `CONFIRMED` must name what
established it and **may not name the attestation of sending**, which is refused by name.

**SILENCE IS NOT AN OBSERVATION.** The record does not say "no bounce was reported", which
would imply someone checked a mailbox. It says the attestation is silent on delivery and
that **nothing here looked** -- and it was written minutes after the send, sooner than a
bounce would necessarily arrive. **The state can still move**: a later bounce sends this to
`DISPATCH_ATTEMPTED_DELIVERY_FAILED`, and that branch was widened to admit it, because a
bounce can follow a dispatch that really happened, so **a failure no longer resets the
count of dispatches**. What a failure forbids is a delivery, a contact and a level.

**THE SENDER IS ATTESTED, NOT CHECKED.** Mission 1.74.5 left the mailbox unbound at the
operator's instruction and **stated that cost in advance**; this is the record of paying
it. The mailbox is in the record because the operator said so, and that is the whole of the
evidence for it. **The approval keeps its placeholder**: writing the real address back into
it would make an unpinned field look pinned and make the mailbox read as approved before
the fact, so the gate refuses that write-back from the execution side.

**NOTHING WAS INVENTED TO FILL A FIELD.** **No message id** -- the attestation carries
none, the only route to one runs through the sending mailbox, the field is `null` and a
non-null value is refused, **because a plausible id is exactly what a fabricated record
would contain**. **No body comparison** -- what left the mail client has not been seen
here. **No reply** -- a reply is a document and would be frozen verbatim in its own record
before anything interpreted it. **No timestamp without an offset**, and a send attested as
happening before its own approval is refused.

**A SENT QUESTION IS STILL NOT AN ANSWER.** R2's verdict is unchanged, 0 residuals closed,
R2 not closed, R1 untouched, and the qualification was not recomputed -- **neither in
general nor from the fact of dispatch**, which is now its own refusal. The v2 packet is
byte-identical, still reads `send_status: NOT_AUTHORIZED` and still records no approval of
its own; the approval's digest recomputes unchanged, which is what the envelope rule was
for.

**1 send by the operator, 1 attestation, 0 deliveries confirmed, 0 provider contacts, 0
replies, 0 emails sent by this repository, 0 connector executions, 0 mailbox searches, 0
message ids, 0 residuals closed, 0 Globalping API executions, 0 measurements, 0 target HTTP
requests, 0 canonical mutations, 0 Claims, 0 Evidence, 0 scores, 0 model calls, 0
documentation requests.** The mission counters stay at zero because **they count what this
repository did**, and the operator's send lives in the execution block where it belongs.
ONYPHE still `NOT_CHECKED_AFTER_DISPATCH`, Netlas still pending, the scanner arc still
parked, ADR-039 untouched.

**Verification.** Gate probed with **97 deliberate violations, 97 caught** (96 by rule, 1
by drift), **0 escaped**, plus **3 of 3 positive controls**. **Six cases repair a hash
before attacking** -- four keep the packet's file hash in step with the edit, two recompute
the spent approval's own digest -- because without them the outer guard caught every such
edit for the same reason and **the checks behind it were never asked anything**. **The
controls are the point**: a delivery confirmed by a source that is NOT the send attestation
passes, and **this send bouncing later** passes, because a gate that could only express
success would force the next outcome to be recorded as something it is not. **Eighteen of
the module's 78 tests now run the gate's own checks against mutated dicts** rather than
reading its source, because **a refusal spelled in a module is not a refusal until
something calls it**. **2979 bare-python tests**; both runners green; `ruff format
--check`, `ruff check` and mypy all run through `uv`; all **48** CI gates.

New: `docs/architecture/mission-1.74.6-report.md`.

Changed: `docs/data/globalping-r2-v2-dispatch-approval-v1.json` records the execution, the
scope and the next action, its approval digest unchanged;
`infrastructure/scripts/render_r2_v2_dispatch_approval.py` gains the `SENT` and delivery
checks; the generated `docs/data/mission-1.74.5-r2-v2-dispatch-approval-v1.md`;
`packages/inferred-claim-evaluator/python/tests/test_r2_v2_dispatch_approval.py` 56 tests
to 78; `docs/CLAUDE.md` 1.115 to 1.116.

Unchanged: the v2 packet is byte-identical including its subject, body, recipient and
content hash; the v1 packet, the v1 approval, the R1 package and every Mission 1.74 record
are untouched; **no new CI gate was added**, because the gate that governs this record
already existed; and no canonical table, source review or ADR was modified.

## 1.114 - 2026-09-06 (Sprint 1 / Mission 1.74.5)

**`R2_V2_DISPATCH_APPROVED_AWAITING_MANUAL_OPERATOR_ACTION`.** The operator approved
exactly one manual email dispatch of the v2 packet to `d@globalping.io`. **Nothing was
sent, no connector was used, and no mailbox was read.**

**A QUOTED DIGEST IS RECOMPUTED, NOT COPIED.** The approval arrived carrying a content
hash, and **copying it would have made the approval name whatever the instruction said
rather than whatever the packet is**. So the digest was recomputed from the packet as
stored, the record keeps BOTH the stated and the recomputed value, and the gate refuses
them disagreeing -- which turns a quoted string into a check that could have failed. It
did not, and the assertion passed silently, which is what a check looks like when the
world is in order.

**THE SENDER STAYS OPEN, AT THE OPERATOR'S EXPLICIT INSTRUCTION**, which is the same
property Mission 1.65 recorded in advance for a manual mail send: the sender is not
determined until the send. The approval binds the enquiry, the packet version, the content
digest, the mechanism, the recipient, the channel, the subject and the send limit, and
**not the sender** -- and a real mailbox written into that field would be a DIFFERENT
approval, which the gate refuses.

**A SECOND APPROVAL IS NOT A RENEWAL OF A SPENT ONE.** The recipient changed and the
recipient is a bound field, so this authorises a different action rather than extending an
exhausted one; the two approvals name different content digests, different recipients and
different approval digests, and **neither can stand in for the other**. **The first
approval was not reused, not reinterpreted and not repaired**: the gate asserts LIVE that
it still reads exhausted, that its attempt still reads a failure and that its
`provider_contacted` still reads false, so **a later edit that quietly rehabilitated the
bounce into a delivery fails here rather than passing quietly**. It gained exactly one
appended forward pointer with its own digest unchanged -- Mission 1.66.1's shape, used for
the third time in this arc.

**THE CEILING BELONGS TO THE MEDIUM, NOT TO THE ADDRESS.** The address changed and the
medium did not, so `BYTE_VERIFIED` stays unreachable, the reachable set is exactly
`OPERATOR_ATTESTED`, and the upgrade path reads **NONE**. Worth saying plainly because the
temptation runs the other way: a NEW channel invites the thought that its properties might
be new too, and a mail client's outbox is something no guard here can observe whichever
address the mail is going to.

**AN APPROVAL TO ASK IS NOT AN ANSWER.** R2's verdict is unchanged, 0 residuals closed,
the qualification was not recomputed, R1 was not touched, and the packet is byte-identical
and still reads `send_status: NOT_AUTHORIZED` while recording no approval of its own --
because the approval lives beside it, which is the discipline that keeps the packet's own
field honest.

**0 send attempts, 0 sends, 0 deliveries, 0 provider contacts, 0 emails sent by this
repository, 0 connector executions, 0 mailbox searches, 0 attestations, 0 residuals
closed, 0 Globalping API executions, 0 measurements, 0 target HTTP requests, 0 canonical
mutations, 0 Claims, 0 Evidence, 0 scores, 0 model calls, 0 documentation requests.**
ONYPHE still `NOT_CHECKED_AFTER_DISPATCH`, Netlas still pending, the scanner arc still
parked, ADR-039 untouched.

**Verification.** Gate probed with **95 deliberate violations, 95 caught** (92 by rule, 3
by drift) plus **3 of 3 positive controls** -- and **the one that matters most is this
approval BOUNCING TOO**, a representable state, because a gate that could only express
success would force the next failure to be recorded as something it is not. **Eleven of
the violation cases attack the SPENT approval rather than this one** -- rehabilitating it
to SENT, resetting it to pending, turning its bounce into a contact, un-exhausting it,
breaking its digest, retargeting it at the new recipient -- and all eleven are refused,
**which is what makes "not a renewal" a check rather than a sentence**. **2944 bare-python
tests**; both runners green; `ruff format --check`, `ruff check` and mypy all run through
`uv`; all **48** CI gates.

New: `docs/data/globalping-r2-v2-dispatch-approval-v1.json`, the generated
`docs/data/mission-1.74.5-r2-v2-dispatch-approval-v1.md`,
`infrastructure/scripts/render_r2_v2_dispatch_approval.py` (CI gate 48),
`packages/inferred-claim-evaluator/python/tests/test_r2_v2_dispatch_approval.py`, and
`docs/architecture/mission-1.74.5-report.md`.

Changed: `docs/data/globalping-r2-dispatch-approval-v1.json` gains **one appended forward
pointer** and no other change; `docs/CLAUDE.md` 1.114 to 1.115; `.github/workflows/ci.yml`
gains one gate.

Unchanged: the v2 packet is byte-identical including its subject, body, recipient and
content hash; the v1 packet, the R1 package and every Mission 1.74 record are untouched;
and no canonical table, source review or ADR was modified.

## 1.113 - 2026-09-06 (Sprint 1 / Mission 1.74.4)

**`R2_DISPATCH_ATTEMPTED_DELIVERY_FAILED_REPLACEMENT_PREPARED`.** The operator attempted
the approved GP-R2-Q1 email exactly once and it was rejected. The approval is spent, a
replacement recipient was reviewed and established, and a second packet is prepared and
**unapproved**.

**A BOUNCE IS NOT A SEND AND IT IS NOT A CONTACT.** `provider_contacted` stays **false**,
because nobody received it -- an attempt that bounced would otherwise put a conversation
in the record that never began. **No attestation level applies either**: the levels grade
evidence that a message WAS delivered, and nothing was, so recording `OPERATOR_ATTESTED`
would grade the evidence for an event that did not happen. The attestation is marked
structurally as being **of a failure rather than of a send**. And **the non-delivery
report was not imported**: reading the operator's mailbox for a bounce would replace an
attestation with an inference and require an access nobody requested -- Mission 1.66's
reasoning, applied to a failure instead of a send.

**THE APPROVAL IS EXHAUSTED BY THE ATTEMPT.** One send was authorised and one was
attempted. A retry to the same address is a second use of a one-use approval; a send to a
different address is **a different action**, because the recipient is a bound field. The
replacement **requires a new explicit operator approval** that does not exist, and the
approval's own digest did not move -- the execution section changed and the binding fields
did not.

**A SUPPLIED ADDRESS IS A CLAIM, AND IS ESTABLISHED ON PROVENANCE OR NOT AT ALL.**
`d@globalping.io` arrived in an instruction, and **that is not why it is accepted**.
Mission 1.65 judged a recipient on provenance rather than on spelling and refused to infer
one from convention; the same standard applies to one handed over. Four first-party
surfaces were read: the **Terms of Use section 16**, the **Privacy Policy section 12** and
the **Cookie Policy** all designate `legal@globalping.io`, and only the website footer
publishes the candidate -- established from the provider's own committed source,
`jsdelivr/globalping.io src/views/components/footer.html`, as the live link
`<li><a href="mailto:d@globalping.io"> d@globalping.io</a></li>`. The rendered homepage
agrees and is recorded as **CORROBORATION ONLY**, because that retrieval went through a
summarising extraction and **a summary is not a document**. **A single-letter local part is
not treated as disqualifying**: a string rule would refuse a correctly established address
while admitting a guessed one that happened to look ordinary.

**AN ESTABLISHED GENERAL CONTACT IS NOT A DESIGNATED CHANNEL**, which is the same over-read
this arc has refused for a schema, for product design and for a FAQ answer.
**`ESTABLISHED_FIRST_PARTY_GENERAL_CONTACT_NOT_THE_TERMS_DESIGNATED_CHANNEL`**: three
provider documents designate the original address and not one designates the footer
address, so calling it designated would assert a standing no provider document gives it.
What makes it relevant is **weaker and is written down as weaker** -- the designated route
is unreachable and this is the only other address the provider publishes. **The tension is
recorded rather than smoothed**: the provider's own current documents designate an address
that does not accept mail while a different address is live on its homepage, and this
record does not resolve that, nor is it evidence that the general address is monitored,
answered or appropriate for a Terms question. **One rejection is not a permanent fact about
an address**: `OPERATOR_ATTESTED_DELIVERY_REJECTED_ONCE`, explicitly not
`PERMANENTLY_NONEXISTENT`.

**THE REPLACEMENT PRESERVES THE APPROVED WORDING EXACTLY.** A sentence explaining the
bounce was considered and NOT added: nothing about the question changes with the
recipient, and adding prose would make this a differently worded enquiry the operator has
not read. **The channel label changed**, because reusing the designated-channel label would
assert a designation this address does not have. **v1 is superseded, not edited** -- it
still answers to its own hash, and it recorded a correctly established address that later
rejected delivery, which is a fact about the provider rather than an error in the record.

**BOTH PACKETS SHARE A QUESTION ID, AND THE HASH IS WHAT DEFEATS THE HAZARD.** The
approval binds `approved_content_sha256` and the digests differ because the recipient and
channel differ, so the spent approval **cannot name** the replacement -- enforced by
arithmetic rather than by a rule somebody has to remember, and checked from both
directions.

**0 emails sent by this repository, 0 connector executions, 0 mailbox searches, 0 emails
delivered, 0 provider contacts, 0 approvals created, 0 residuals closed, 0 qualifications
recomputed, 0 Globalping API executions, 0 measurements, 0 canonical mutations, 0 Claims,
0 Evidence, 0 scores, 0 model calls.** Failed delivery attempts **by the operator**: **1**,
counted separately, because this repository acting and the operator acting are different
facts. Six first-party documentation requests. R1 untouched at `SENT` / `OPERATOR_ATTESTED`.

**Verification.** Both gates probed with **64 deliberate violations, 64 caught** (61 by
rule, 3 by drift) plus **4 of 4 positive controls** -- **one of them inverted and it is the
important one**: a review that establishes NOTHING must BLOCK the packet bound to it, so
three controls prove legitimate variants pass and one proves an unestablished address is
refused. **The probe's writes are now all retried**: this machine intermittently rejects
writes to these files, and a probe that dies mid-case leaves a record edited on disk --
Mission 1.67's finding, met three times in this arc, and hardening `restore()` alone was
not enough because the crash happened on a CASE write. **Four Mission 1.74.2 tests
asserted the pre-attempt state and were re-pointed rather than deleted**, one of which
iterated every accounting counter asserting zero and now excludes the counter the OPERATOR
owns. **2901 bare-python tests**; both runners green; `ruff format --check`, `ruff check`
and mypy all run through `uv`; all **47** CI gates.

New: `docs/data/globalping-r2-replacement-recipient-review-v1.json`,
`docs/data/globalping-r2-enquiry-packet-v2.json`, the generated
`docs/data/mission-1.74.4-r2-replacement-packet-v1.md`,
`infrastructure/scripts/render_r2_replacement_packet.py` (CI gate 47),
`packages/inferred-claim-evaluator/python/tests/test_r2_replacement_packet.py`, and
`docs/architecture/mission-1.74.4-report.md`.

Changed: `docs/data/globalping-r2-dispatch-approval-v1.json` execution section records the
failed attempt, its approval digest and every binding field unchanged;
`infrastructure/scripts/render_r2_dispatch_approval.py` gains the failure status and its
rules; four tests re-pointed; `docs/CLAUDE.md` 1.113 to 1.114.

Unchanged: **both R2 enquiry packet v1 and the R1 package are byte-identical**, every
Mission 1.74 record is untouched, and no canonical table, source review or ADR was
modified.

## 1.112 - 2026-09-06 (Sprint 1 / Mission 1.74.3)

**`R1_SENT_OPERATOR_ATTESTED_BYTE_VERIFICATION_NOT_REACHED`.** The operator posted the R1
issue once, manually, and attested to it. The execution record moved to `SENT`. **This
repository created nothing, invoked no `gh`, and made no GitHub API call.**

**THE SUPPLIED ISSUE NUMBER WAS A PLACEHOLDER AND NO NUMBER WAS INVENTED.** The
attestation read `issue_number: XXXX`, the template line unfilled. The URL already
carries it, so `907` is **derived from the URL** and recorded as such -- the two are the
same fact stated once rather than an independent confirmation. Both the placeholder and
the derivation are in the record, and the validator now refuses a number that disagrees
with its own URL.

**`BYTE_VERIFIED` WAS REACHABLE AND WAS NOT REACHED, AND THE REASON IS MISSION 1.63.**
Mission 1.74.1 established that this channel CAN be byte-verified, so the obvious move was
to fetch the issue and claim the upgrade. **The page was fetched and the upgrade was
refused anyway**, because the retrieval went through an HTML-to-markdown conversion AND a
summarising model -- and **a retrieval summary is not a document** where a sentence
decides a gate. The extraction rendered the body's paragraph break as a space, which is an
artifact of the conversion rather than evidence of a difference, and **precisely because
it is an artifact, that retrieval cannot distinguish it from one.** What the fetch bought
is recorded as CORROBORATION with its limit stated: the issue exists, it is open, its
author is the approved identity, its repository and number match, and **its title matched
character for character**. What it does not establish is byte equality of the body.

**A DEFECT IN THIS PROJECT'S OWN R2 GATE WAS SURFACED BY THE FIRST LEGITIMATE
TRANSITION.** Mission 1.74.2's gate compared the R1 execution state LIVE against a
snapshot it had taken when it was written, so **it refused the very transition the R1
approval was designed to make** -- proved by running it against a mutated copy before
changing anything. The repair is not a loosening: what that gate is entitled to assert is
that MISSION 1.74.2 did not move it, which is history and is kept in a field now named
`r1_execution_state_when_this_was_written`, plus that the R1 approval's BINDING fields and
digest are untouched, which it already checked and which is the property that actually
matters. **The value was preserved and only the name and the comparison changed**, and a
new check replaces the removed one: R1 may not record more posts than R1 authorised.

**THE R1 GATE GOT STRICTER, NOT LOOSER.** A `SENT` record must now name its attester,
carry an issue URL on a channel that produces one, have that URL parse and name the
approved repository, have its number agree with its own URL, and **state whether the body
was compared raw**. That last rule closed a probe escape: deleting `raw_body_compared`
slipped through because the check only fired for `BYTE_VERIFIED`, so a `SENT` record could
leave a reader unable to tell an unverified send from an unrecorded verification.

**A CRASHED PROBE LEFT A RECORD EDITED AND THE GATE CAUGHT IT.** The Mission 1.74.2 probe
hit an intermittent file lock, its restore raised, and it left `PROVIDER_CONTACTS: 1` in
the R2 approval on disk; **the gate refused it on the next run**. That is Mission 1.67's
finding recurring -- a restore that can fail silently leaves a record edited -- and the new
probe **retries and then proves every file is back** rather than assuming the write
succeeded.

**AN ANSWER HAS NOT ARRIVED.** The issue is open, R1's verdict is unchanged at
`R1_PARTIAL_IMPLEMENTATION_ONLY`, the tally is still 10 PASS / 2 PARTIAL / 0 FAIL, and
`COUNTERPART_UNRESOLVED` stands. **A sent question is still not an answer**, and R2 still
reads `PENDING_MANUAL_OPERATOR_ACTION` with 0 sends.

**0 issues created by this repository, 0 gh invocations, 0 GitHub API calls, 0 emails
sent, 0 mail connector executions, 0 mailbox searches, 0 residuals closed, 0
qualifications recomputed, 0 Globalping API executions, 0 measurements, 0 target HTTP
requests, 0 canonical mutations, 0 Claims, 0 Evidence, 0 scores, 0 model calls, 0
embeddings, 0 migrations.** Public page retrievals by this repository: **1**, recorded
rather than glossed. ONYPHE still `NOT_CHECKED_AFTER_DISPATCH`, Netlas still pending, the
scanner arc still parked, ADR-039 untouched.

**Verification.** Both gates probed with **42 deliberate violations, 42 caught** (39 by
rule, 3 by drift) plus **4 of 4 positive controls** -- one proving a properly evidenced
`BYTE_VERIFIED` record IS accepted, so the gate did not merely move its floor, and another
proving the pre-transition `PENDING` state is still representable, because **a gate that
only accepts the state we happen to be in is not a gate**. **One escape found and closed
by adding a rule.** **Five tests asserted the pre-transition state and were re-pointed
rather than deleted**, to the property rather than the incidental value: a test asserting
an execution never happens is a test asserting the approval is never used. **2857
bare-python tests**; both runners green; `ruff format --check`, `ruff check` and mypy all
run through `uv`; all **46** CI gates.

New: `docs/architecture/mission-1.74.3-report.md`.

Changed: `docs/data/globalping-r1-dispatch-approval-v1.json` execution section moves to
`SENT`, its approval digest and every binding field unchanged;
`docs/data/globalping-r2-dispatch-approval-v1.json` renames one scope field and preserves
its value; `infrastructure/scripts/render_r1_dispatch_approval.py` gains six `SENT` rules;
`infrastructure/scripts/render_r2_dispatch_approval.py` has its live coupling corrected;
both generated pages re-render; five tests re-pointed and four added;
`docs/CLAUDE.md` 1.112 to 1.113.

Unchanged: both enquiry packets are byte-identical, every Mission 1.74 record is untouched,
the gate count stays at 46, and no canonical table, source review or ADR was modified.

## 1.111 - 2026-09-06 (Sprint 1 / Mission 1.74.2)

**`R2_DISPATCH_APPROVED_AWAITING_MANUAL_OPERATOR_ACTION`.** The operator approved
dispatch of **GP-R2-Q1** by `OPERATOR_MANUAL_EMAIL` to `legal@globalping.io`, the address
the Terms designate in section 16. **This repository sent nothing, used no connector and
searched no mailbox.**

**THE RULES INVERT AGAINST MISSION 1.74.1, AND THAT IS THE FINDING.** R1 was a public
GitHub issue: every field of the action pinned, `BYTE_VERIFIED` reachable. R2 is a manual
email: the sender **not** pinned, `BYTE_VERIFIED` **unreachable**. **Both differences are
properties of the CHANNEL rather than of manual sending**, which is why this is a separate
gate rather than the same one pointed at another file -- a gate accepting the same
evidence for both would be asserting something false about one of them.

**THREE FIELDS OF FOUR, AND THE COST WAS STATED IN ADVANCE.** Mission 1.65 wrote it down
before anyone knew whether it would matter: under a manual mail send the sender genuinely
is not determined until the send, so the hash pins three of four. Mission 1.66.1 then paid
exactly that, admitting the sender under `ALLOWED_BY_APPROVED_PLACEHOLDER`. **Mission
1.74.1 escaped it** because a public repository and a GitHub identity are determined
before the act; **here it recurs**, and pinning the fourth field would produce a different
approval that supersedes this one rather than editing it. The validator refuses a real
mailbox in the sender field for exactly that reason.

**`BYTE_VERIFIED` IS UNREACHABLE, AND THE RECORD SAYS SO RATHER THAN IMPLYING A PATH THAT
DOES NOT EXIST.** A public issue has a durable URL; a mail client's outbox is something no
guard here can observe, which is what Mission 1.66 established. So the reachable set is
exactly `OPERATOR_ATTESTED` and the upgrade path reads **NONE**. Importing a sent-message
artifact from the operator's own mailbox was considered and refused on Mission 1.66's
reasoning: it would replace an attestation with an inference and require an access nobody
requested. **This gate REFUSES `BYTE_VERIFIED` where the R1 gate REQUIRES that it be
possible**, and a test asserts the two gates disagree on that field, because if they ever
agreed one of them would be wrong.

**THE CONNECTOR WAS AVAILABLE THROUGHOUT AND WAS NOT USED.** One call would have produced
matching text, a matching recipient and a verifying content hash -- **and a different
action**, because the channel is a bound field and the sender would be a mailbox the
operator never named. **A connector present in the runtime is still not channel
authorisation.**

**TWO APPROVALS, AND THEY ARE NOT ONE.** Each names its own enquiry, mechanism and
recipient, and each authorises exactly one act. **The R1 approval's binding fields are
untouched and its digest still recomputes**; it gained exactly one appended forward
pointer naming this record, which is Mission 1.66.1's shape -- the stale-record hazard
closed by appending rather than by editing what an earlier record established. Because the
packets are never edited, **the R1 gate stayed green throughout**: its check that the R2
packet still reads `NOT_AUTHORIZED` is a check that the packet was not edited, and the
discipline is what keeps it valid.

**AN APPROVAL TO ASK IS NOT AN ANSWER.** R2's verdict is unchanged, no residual closed,
the qualification was not recomputed, the tally is still 10 PASS / 2 PARTIAL / 0 FAIL with
`COUNTERPART_UNRESOLVED`, and Mission 1.74's closure still reads `enquiries_sent: 0` and
`residuals_remaining: 2`.

**0 emails sent, 0 mail connector executions, 0 mailbox searches, 0 public posts, 0 GitHub
issues, 0 gh invocations, 0 provider contacts, 0 enquiries sent, 0 Globalping API
executions, 0 measurements, 0 target HTTP requests, 0 accounts, 0 tokens, 0 credential
reads, 0 documentation requests**, 0 sources registered, 0 canonical mutations, 0 Claims,
0 Evidence, 0 scores, 0 model calls, 0 embeddings, 0 migrations. ONYPHE still
`NOT_CHECKED_AFTER_DISPATCH`, Netlas still pending, the scanner arc still parked, ADR-039
untouched.

**Verification.** Gate probed with **108 deliberate violations, 108 caught** (104 by rule,
4 by drift) plus **4 of 4 positive controls**. **One control's name claimed more than it
tested and was corrected rather than kept**: it was called a pinned-sender supersession and
never pinned the sender -- which this gate must refuse outright -- so it was renamed to
what it proves, an approval superseded before any send. Mission 1.65's rule applied to a
probe's own honesty rather than to a record's. **A missing field is a refusal rather than a
crash**, carried forward from 1.74.1 and proved again with five cases. **The R1 gate was
re-run after the forward pointer was appended** and stays green with its digest unchanged.
**58 new tests**, taking the bare-python runner to **2853**; both test runners green; `ruff
format --check`, `ruff check` and mypy all run through `uv`; all **46** CI gates.

New: `docs/data/globalping-r2-dispatch-approval-v1.json`, the generated
`docs/data/mission-1.74.2-r2-dispatch-approval-v1.md`,
`infrastructure/scripts/render_r2_dispatch_approval.py` (CI gate 46),
`packages/inferred-claim-evaluator/python/tests/test_r2_dispatch_approval.py`, and
`docs/architecture/mission-1.74.2-report.md`.

Changed: `docs/CLAUDE.md` 1.111 to 1.112; `.github/workflows/ci.yml` gains one gate; and
`docs/data/globalping-r1-dispatch-approval-v1.json` gains **one appended forward pointer**
and no other change.

Unchanged: both enquiry packets are byte-identical, every Mission 1.74 record is untouched,
the R1 approval's binding fields and digest are untouched, and no canonical table, source
review or ADR was modified.

## 1.110 - 2026-09-06 (Sprint 1 / Mission 1.74.1)

**`R1_DISPATCH_APPROVED_AWAITING_MANUAL_OPERATOR_ACTION`.** The operator approved
dispatch of **GP-R1-Q1 only**, by a named mechanism, and **this repository performed no
outward action**: `OPERATOR_MANUAL_GITHUB_ISSUE`, one public issue on
`jsdelivr/globalping` under `@Speekyx`, carrying the frozen title and body.

**THE APPROVAL IS RECORDED BESIDE THE PACKET AND NOT INSIDE IT.** Mission 1.66 settled
that marking a frozen document APPROVED changes the bytes that were approved -- and here
it would not even have moved the packet's digest, since that covers only the six binding
fields, **and it would still have changed the artifact the operator read**. So the packet
is byte-identical, and the approval names it by a hash **recomputed from the packet as
stored** rather than asserted, plus the packet's own file hash so a later edit is
detectable. **The packet's `send_status: NOT_AUTHORIZED` therefore still reads
correctly**: that field means THIS DOCUMENT RECORDS NO AUTHORIZATION and never that no
authorisation exists -- the distinction Mission 1.66 wrote down, load-bearing for the
first time.

**EVERY FIELD OF THE ACTION IS PINNED, AND THAT IS WHERE THIS DIFFERS FROM THE ONYPHE
ARC.** Mission 1.65 stated its cost in advance: the ONYPHE envelope bound a
**placeholder** sender, because under manual email the sender is not determined until the
send, so the hash pinned three fields of four -- and Mission 1.66.1 paid exactly that
cost, matching on recipient, channel and subject while the sender matched nothing. **It
does not recur here.** The destination is a public repository rather than a mailbox, so
mechanism, target, identity and title are all determined before the act and the approval
digest binds all of them; changing any one produces a **different approval that
supersedes this one rather than editing it**. The digest excludes itself, the execution
status and the recorded date.

**AN APPROVAL IS NOT AN EXECUTION, AND IT IS UNUSUALLY EASY TO LOSE HERE**: once the
approval exists, **every field an execution record needs is already known**, so a record
could fill itself in completely and be entirely fictional. `PENDING_MANUAL_OPERATOR_ACTION`,
**0 public posts, no issue URL, 0 issues created by this repository, 0 `gh` invocations,
0 GitHub API calls, no attestation.** `SENT` is reachable only through an explicit
operator attestation that the post was made.

**`BYTE_VERIFIED` IS REACHABLE HERE, AND SAYING WHY IS WORTH MORE THAN THE UPGRADE.**
Mission 1.66 could reach only `OPERATOR_ATTESTED`, because a manual email send happens
inside a mail client nothing here can observe, and Mission 1.66.1 recorded that ceiling
honestly. A public issue has a **durable public URL**, so once the operator supplies it
the posted title and body can be compared against the approved ones. **That ceiling was a
property of the CHANNEL rather than of manual sending.**

**THE INTEGRITY CHECKS ARE FROZEN BEFORE ANY POST**, which is the only time they mean
anything: title, body and repository must match, **one approval authorises exactly one
public post**, a second post is **reported as a duplicate rather than tidied away**
because a posted issue cannot be unposted, and a divergence never repairs the approval.

**ONE APPROVAL COVERS ONE ENQUIRY.** `GP-R2-Q1` was prepared alongside it and is **not**
approved; its packet is byte-identical and still reads `NOT_AUTHORIZED`. R2 dispatch
requires its own approval.

**MISSION 1.74 WAS NOT REWRITTEN.** Its closure still reads `enquiries_sent: 0`,
`residuals_remaining: 2` and `dispatch_authorised_by_this_mission: false` -- all true when
it ran and still true, because the approval arrived afterwards and lives in its own
document. **An approval to ask is not an answer**: R1's verdict is unchanged at
`R1_PARTIAL_IMPLEMENTATION_ONLY`, the qualification was not recomputed, and the tally is
still 10 PASS / 2 PARTIAL / 0 FAIL with `COUNTERPART_UNRESOLVED`.

**0 public posts, 0 GitHub issues created, 0 `gh` invocations, 0 emails sent, 0 mailbox
searches, 0 provider contacts, 0 enquiries sent, 0 Globalping API executions, 0
measurements, 0 target HTTP requests, 0 accounts, 0 tokens, 0 credential reads, 0
first-party document requests**, 0 sources registered, 0 governance mutations, 0
canonical mutations, 0 Claims, 0 Evidence, 0 independence groups, 0 reliability values, 0
scores, 0 model calls, 0 embeddings, 0 migrations. ONYPHE still
`NOT_CHECKED_AFTER_DISPATCH`, Netlas still pending, the scanner arc still parked, ADR-039
untouched.

**Verification.** Gate probed with **89 deliberate violations, 89 caught** (86 by rule, 3
by drift) plus **4 of 4 positive controls** -- including a correctly evidenced
`BYTE_VERIFIED` send, which is ACCEPTED, because **a gate that refuses everything is not a
gate**. **A missing field is a refusal rather than a crash**: five cases delete a field the
gate reads and each is refused, so a truncated record cannot skip a check by not carrying
its subject -- a defect found by the first render raising `KeyError` on a lookup pointing
at the wrong block. **57 new tests**, taking the bare-python runner to **2795**; both test
runners green; `ruff format --check`, `ruff check` and mypy all run through `uv`; all
**45** CI gates.

New: `docs/data/globalping-r1-dispatch-approval-v1.json`, the generated
`docs/data/mission-1.74.1-r1-dispatch-approval-v1.md`,
`infrastructure/scripts/render_r1_dispatch_approval.py` (CI gate 45),
`packages/inferred-claim-evaluator/python/tests/test_r1_dispatch_approval.py`, and
`docs/architecture/mission-1.74.1-report.md`.

Changed: `docs/CLAUDE.md` 1.110 to 1.111; `.github/workflows/ci.yml` gains one gate.

Unchanged: both enquiry packets are byte-identical, every Mission 1.74 record is
untouched, and no canonical table, source review or ADR was modified.

## 1.109 - 2026-09-06 (Sprint 1 / Mission 1.74)

**`GLOBALPING_TWO_PROVIDER_CLARIFICATIONS_REQUIRED`.** Both residuals were pursued to the
end of the public record, both narrowed, and **neither closed**. The tally is unchanged at
**10 PASS / 2 PARTIAL / 0 FAIL**, and the mission's product is two frozen, hashed,
**unsent** questions.

**THE R1 FINDING IS THAT EVERYTHING POINTS THE SAME WAY AND NOTHING COMMITS THE
PROVIDER.** Mission 1.73 checked one surface; this checked **five**, and the specification
was re-verified on the retrieved bytes rather than on a summary -- 124,793 bytes, **zero**
case-insensitive matches for `redirect`, **zero** for `3xx`, and **byte-identical to the
Mission 1.73 copy**. The 27 `Location` matches are the API's own asynchronous-measurement
header and example keys such as `pingLocations`, not an HTTP redirect Location. The two
other repositories' matches are OAuth redirect URIs and site routing middleware. **No
provider test asserts HTTP measurement redirect behaviour**: the single match in the probe
repository is an adoption-server test.

**AND A MAINTAINER STATEMENT WAS FOUND THAT POINTS THE RIGHT WAY AND STILL DOES NOT CLOSE
IT.** In the provider's own issue #347 a maintainer writes that *the body may be empty in
some cases, most often redirects and error responses* -- which **presupposes that a
redirect response appears in a Globalping result**, exactly what a non-following apparatus
produces. It is graded `PROVIDER_MAINTAINER_STATEMENT_INCIDENTAL` and it did not upgrade
the evidence level, because it defines nothing, promises nothing, and appears in a
discussion about `rawOutput` formatting. **A closing verdict needs a normative provider
contract, and an incidental premise in an issue about output formatting is not one,
however strongly it points the right way.** `R1_PARTIAL_IMPLEMENTATION_ONLY` at
`R1_C_IMPLEMENTATION_OBSERVED`, and **zero matches for a word mean the word is absent from
a reviewed surface, never that the behaviour is absent from the apparatus**.

**R2 SPLIT IN TWO, AND ONLY ONE HALF CLOSED.** R2-A closes positively on the provider's
own FAQ, read from the website's committed source rather than from a rendered shell: asked
*Can I use credits to power a commercial tool or product?*, the provider answers *Yes, we
support commercial use of Globalping within the limits of our terms of service.*
**`COMMERCIAL_USE_GENERAL_PERMITTED_WITHIN_TERMS`** -- and the answer's own qualifier is
what bounds it. *Within the limits of our terms of service* **defers to the Terms for
everything other than commerciality**, so it settles WHETHER we may be a commercial user
and says nothing about WHAT we may point the service at. Reading it as third-party-target
permission is the cheap move this mission most had to refuse.

**R2-B DID NOT CLOSE, AND THE ONE HOOK THAT COULD HAVE WIDENED IT WAS FOLLOWED.** Section
2 Permitted Use reads *Globalping works as a platform that allows you to monitor, debug,
and benchmark your internet infrastructure using a globally distributed network of
probes* -- **descriptive in form, under a heading that reads as a limitation**, with no
*only* and no *solely*, and the two readings reconciled nowhere. Section 5 Prohibited Use
prohibits nothing relevant, which cuts toward descriptive; the heading and the word *your*
cut the other way. Then Section 1 Definitions says *the Globalping platform further
described on the Website*, so **the Terms incorporate the Website's description by
reference** -- and the homepage says *Monitor, debug and benchmark your internet
infrastructure from a globally distributed network of probes.* **The hook was followed
looking for a widening and the incorporated text repeats the same narrowing, which is a
stronger finding than not having looked.** `THIRD_PARTY_TARGET_SCOPE_UNRESOLVED`.

**THREE READINGS WERE AVAILABLE AND ALL THREE REFUSED.** The API schema's *A publicly
reachable measurement target* is `TECHNICAL_TARGET_VALIDATION_ONLY`, because **the
provider nowhere states that acceptance by the schema is permission under the Terms**. The
probe README's *We block private IP addresses as targets* presupposes public endpoints and
is product design rather than a grant. And Section 3's reservation of *all rights that are
not expressly granted* sits in a proprietary-rights section about the look and feel of the
Website: it is **not read as everything-unmentioned-is-prohibited, and not ignored
either**.

**THE PROJECT MAY REFUSE UNDER AMBIGUITY, AND THAT IS GOVERNANCE RATHER THAN A LEGAL
CONCLUSION.** `PROVIDER_TERMS_REQUIRE_CLARIFICATION`: the Terms do **not** block the
intended activity, and that is **not the same as permission**. Outcome G was available and
refused for exactly that reason, because an ambiguous Permitted Use section is not an
explicit prohibition. Outcome H was refused too: every signal points at not following
redirects, which is what the SROS side would want, so **what is missing is the commitment
rather than the compatibility**.

**TWO ENQUIRIES, BECAUSE TWO PROVIDER-DESIGNATED CHANNELS ARE GENUINELY REQUIRED.** R1 is
a technical contract question and the provider maintains a public issue tracker where
maintainers answer such questions; R2 is a Terms question and **the Terms themselves
designate `legal@globalping.io` in Section 16**. One packet could not have carried both
without sending a Terms question to a technical channel. Each is frozen, each answers to a
recomputed SHA-256 over its binding fields -- **excluding its own digest, its send status
and its recorded date**, which is Mission 1.65's envelope rule -- and each records why the
public documentation is insufficient and what answer would discriminate. **`send_status`
is `NOT_AUTHORIZED` on both, `ENQUIRIES_SENT` is 0, no operator approval is recorded, and
this mission authorises no dispatch.**

**GOVERNANCE DID NOT BEND TO MAKE A PROVIDER PASS.** ADR-039's HEAD transport route, body
retention restriction, source-collection precedence, robots policy, target exclusions,
load limits and run-authorization separation are all preserved, the GET route is still
incompatible with the initial profile, and Mission 1.72's `BODY_PERSISTENCE_DEFAULT` is
still `DISABLED`. **No PASS dimension was reopened**, because no contradicting evidence
was found; C4 was incidentally reinforced by the same issue that supplied the maintainer
statement.

**Q1 STAYS `PROMISING_BUT_ROUTE_QUALIFICATION_REQUIRED`**, failing on the one condition it
has always failed on, with **0 independence groups**, `PAIR_ANALYSIS_NOT_READY`, no class
selected and `selected-quantity-class-v1.json` still absent. **Registry unchanged at 15**
for a fourth mission running: nothing new was observed to register.

**13 of 18 first-party documentation requests, 2 of which returned nothing usable and are
counted. 0 Globalping API executions, 0 measurements created or read, 0 probe runs, 0
target HTTP requests, 0 SROS fetcher runs, 0 target-value exposures, 0 accounts, 0 tokens,
0 trials, 0 purchases, 0 credential reads, 0 mailbox searches, 0 enquiries sent, 0
provider contacts, 0 alternative counterparts evaluated**, 0 sources registered, 0
governance mutations, 0 canonical mutations, 0 thresholds, 0 Claims, 0 Evidence, 0
independence groups, 0 reliability values, 0 scores, 0 model calls, 0 embeddings, 0
migrations, 0 constructs selected, 0 quantity classes selected. ONYPHE still
`NOT_CHECKED_AFTER_DISPATCH`, Netlas still pending, the scanner arc still parked.

**Verification.** Validator probed with **207 deliberate violations, 207 caught** (203 by
rule, 4 by drift) plus **7 of 7 positive controls, all variants rather than the shipped
bytes**. **One escape was found and closed by adding a rule rather than by editing a
record**: the R2 sub-results had no vocabulary, so a bogus value slid past a
correspondence check that only fired on the good value; a sub-result is now a restatement
of its review's verdict, and each half of the R2 conjunction must follow its own
sub-result. **116 new tests**, taking the bare-python runner to **2738**; both test runners green; `ruff format --check`, `ruff check`
and mypy all run through `uv`; all **44** CI gates.

New: `docs/data/mission-1.74-baseline-v1.json`,
`docs/data/mission-1.74-documentation-ledger-v1.json`,
`docs/data/globalping-redirect-contract-review-v1.json`,
`docs/data/globalping-provider-terms-scope-review-v1.json`,
`docs/data/globalping-commercial-purpose-review-v1.json`,
`docs/data/globalping-third-party-target-scope-review-v1.json`,
`docs/data/globalping-residual-closure-v1.json`,
`docs/data/globalping-counterpart-qualification-v2.json`,
`docs/data/q1-two-route-readiness-v2.json`,
`docs/data/quantity-class-selection-decision-v4.json`,
`docs/data/globalping-r1-enquiry-packet-v1.json`,
`docs/data/globalping-r2-enquiry-packet-v1.json`, the generated
`docs/data/mission-1.74-globalping-residuals-v1.md` and
`docs/data/globalping-redirect-evidence-v1.md`,
`infrastructure/scripts/render_globalping_residuals.py` (CI gate 44),
`packages/inferred-claim-evaluator/python/tests/test_globalping_residuals.py`, and
`docs/architecture/mission-1.74-report.md`.

Changed: `docs/CLAUDE.md` 1.109 to 1.110; `.github/workflows/ci.yml` gains one gate.

Unchanged: Mission 1.73's `independent-http-counterpart-qualification-v1.json`,
`q1-two-route-readiness-v1.json` and `quantity-class-selection-decision-v3.json` are
superseded rather than edited; ADR-039, the apparatus requirement registry, the source
registry and every canonical table are untouched.

## 1.108 — 2026-09-06 (Sprint 1 / Mission 1.73)

**`COUNTERPART_FOUND_REQUEST_CONTRACT_UNRESOLVED`.** An independent HTTP producer exists,
it was identified on first-party evidence, and it is two narrow questions short of
qualifying. **Ten of twelve mandatory dimensions PASS. Zero FAIL.**

**THE MISSION'S REAL SHIFT IS TEMPORAL AND IT DISSOLVES THE PROBLEM RATHER THAN SOLVING
IT.** Every apparatus this arc examined since Mission 1.58 died on the temporal object: a
maintained current-state view, or a historical snapshot whose coverage nobody documents.
A counterpart that measures **on demand** needs no history at all. The window becomes
prospective by construction -- freeze the corpus and the contracts, authorise, then both
apparatuses receive their targets inside a bounded W -- and `createdAt` and `updatedAt`
are REQUIRED fields on the provider's own measurement response.

**THE CANDIDATE IS GLOBALPING, AND WHAT PASSES IS EVERY PROPERTY MISSION 1.70 COULD NOT
BUY EXTERNALLY.** The operator supplies the exact target -- *A publicly reachable
measurement target* -- with `path`, `query` and an optional `host` override, so the
provider selects no sample and runs no discovery. Its probes perform the request
themselves: *a globally distributed network of community-hosted probes, allowing anyone
to run network testing commands like ping or traceroute from any location*, dispatching
through undici in the provider's own source. Its per-result statuses are `in-progress`,
`finished`, **`failed`** and **`offline`** -- the last defined as a test *where the
requested probe was not available to run the test* -- so **the provider names apparatus
missingness itself rather than leaving us to infer it**. Locations are selectable by
continent, region, country, state, city, ASN, network and tags. And 250 free tests an
hour without authentication covers a 500-target pilot inside the six-hour run bound the
project set itself in Mission 1.72.

**MINIMIZATION IS ACHIEVED BY THE REQUEST RATHER THAN BY TRUSTING A FILTER**, which is
the nicest fit of the mission: the default method is **HEAD**, a HEAD response has no
body, and `rawBody` is documented as *The raw HTTP response body or `null` if there was
no body in response.* So ADR-039's transport-level condition is satisfied by choosing
what to ask rather than by asking the provider to omit something. **Under GET it would
not be**, and that is recorded as a constraint on the future request contract rather
than smoothed away.

**THE FIRST RESIDUAL IS ONE WORD THAT IS NOT IN A 124,793-BYTE SPECIFICATION: REDIRECT.**
The result schema carries one `statusCode` and one header set with no hop array. The
probe source dispatches through `undici.Client.dispatch()`, which does not follow
redirects -- **and that is an observed implementation, not a documented contract.** The
distinction is not pedantry: an undocumented default can change without notice, and if
the counterpart began following redirects while SROS did not, both routes would still
report *a* status and **the divergence would be invisible in the data**. Mission 1.70
closed the external pair on a redirect semantic that WAS documented; §25 of this brief
names *undocumented redirects* as exactly the case where equivalence may not be assumed.

**THE SECOND RESIDUAL IS A SCOPE SENTENCE, AND THE CLAUSE THAT LOOKS DECISIVE IS NOT THE
ONE THAT BITES.** The Terms of Use say *You agree not to use the Services for any
commercial or business purposes* -- under the heading **"If you are a consumer user:"**,
with a separate liability clause addressing business users immediately above. Reading a
consumer-scoped liability clause as a blanket prohibition would be the mirror of the
over-read this project refused in Mission 1.45, where a recommendation to seek legal
advice was not treated as a grant. **Prohibited Use prohibits neither commercial use nor
automated access.** What does bite is §2 Permitted Use: the platform *allows you to
monitor, debug, and benchmark **your** internet infrastructure*, while §3 reserves *all
rights that are not expressly granted*. Measuring a frozen corpus of third-party sites is
not our own infrastructure, and a reservation clause makes the absence of an express
grant weigh more rather than less. **`DEDICATED_GOVERNANCE_REVIEW_REQUIRED`**: neither
clearly blocked nor granted.

**THE TERMS WERE BEHIND THREE NAVIGATION SHELLS AND ARE COMMITTED AS MARKDOWN IN THE
PROVIDER'S OWN REPOSITORY.** Three retrievals of the published pages returned navigation
only; the same document reads in full in version control. **A document automated
retrieval cannot reach is not necessarily a document that does not exist**, and that is
worth carrying: Missions 1.67 and 1.72 both recorded terms as unreachable.

**THE OUTCOME FITS IMPERFECTLY AND THE RECORD SAYS SO** rather than choosing the label
whose wording bends most easily. Outcome D names request semantics, and there are TWO
independent unresolved mandatory gates; reporting D alone would let a reader conclude
that one sentence about redirects unlocks the route. **Outcome I was refused as a
serious understatement** -- an independent, directable, transport-level producer with
legible missingness and prospective temporal semantics WAS identified, and reporting
*none found* would send the next mission hunting for what it already holds, which is the
mistake Mission 1.69 refused. **A, B, C, F, G and H were each refused with their
reasons**: H requires an OTHERWISE VIABLE route, and this one is not otherwise viable.

**PRODUCER IDENTITY WAS DECIDED ON ARCHITECTURE RATHER THAN BRANDING**:
`PROVIDER_OPERATED_OPEN_SOURCE_ENGINE`, because the provider authors the code and
coordinates the network while volunteers host the hardware. No third-party measurement
upstream, no shared observation upstream with SROS, and the auxiliary sharing that does
exist -- DNS, trust stores, the internet -- is recorded as **not** defeating
independence. **The registry's own frame-uniformity rule is met explicitly**: *You may
not modify the probe's code or behavior in any way.*

**Q1 STAYS `PROMISING_BUT_ROUTE_QUALIFICATION_REQUIRED`.** Three of §48's four viability
conditions hold and the fourth is a qualified counterpart, so **no class was selected and
`selected-quantity-class-v1.json` does not exist.** No construct, no counterpart
selected, **0 independence groups**, `PAIR_ANALYSIS_NOT_READY`.

**THE CANDIDATE REGISTRY RULE WAS REVIEWED AND NOT ADDED FOR A NEW REASON**: the
counterpart does not exhibit the failure. Its statuses distinguish apparatus trouble from
target observation, so a candidate that **avoids** a failure mode is not a second
empirical instance of it. **Registry unchanged at 15.**

**26 of 30 documentation requests, 11 of which returned nothing usable and are counted.
0 counterpart API executions, 0 target HTTP requests, 0 SROS fetcher runs, 0 external
measurement jobs, 0 Common Crawl queries, 0 BigQuery, 0 target-value exposures, 0
accounts, 0 trials, 0 purchases, 0 credential reads, 0 mailbox searches, 0 enquiries
sent**, 0 sources registered, 0 canonical mutations, 0 thresholds, 0 Claims, 0 Evidence,
0 independence groups, 0 reliability values, 0 scores, 0 model calls, 0 embeddings, 0
migrations. ADR-039 untouched, the source-collection gate unchanged, ONYPHE still
`NOT_CHECKED_AFTER_DISPATCH`, Netlas still pending, scanner arc parked.

**Verification.** Validator probed with **153 deliberate violations, 153 caught** (150 by
rule, 3 by drift) plus **7 of 7 positive controls, all variants**. **Two defects in my own
control models were found by the validator refusing them**, and both were fixed on my
side rather than by loosening a rule: a serious-candidate count that excluded a candidate
which had been seriously evaluated and then qualified, and a control asserting a state
§48 makes unrepresentable -- all four viability conditions met with Q1 not viable.
**90 new tests**; **2622 bare-python tests**; all pytest suites passed with the database
unchanged; `ruff format --check`, `ruff check` and mypy all run through `uv`; all **43**
CI gates.

## 1.107 — 2026-09-06 (Sprint 1 / Mission 1.72)

**`PUBLIC_HTTP_OBSERVATION_GOVERNANCE_TRACK_READY`.** All five decisions Mission 1.71
left open are resolved, **ADR-039** adopts a distinct governance track, and **nothing is
authorized to run.**

**THE DECISION IS CONDITIONAL, AND THE CONDITION IS WHAT MAKES IT DEFENSIBLE RATHER THAN
CONVENIENT.** The track is available only while the retained material is transport-level;
the moment a response body is retained, the retained thing IS the publisher's material
and source-collection governance applies instead. **GOV-1 is therefore not independent of
GOV-3**, and had GOV-3 chosen full-response retention this ADR would not have been
adoptable at all.

**THE DISTINCTION WAS TESTED RATHER THAN ASSERTED.** If the page's content were entirely
different and the transport outcome identical, the observation does not change; if the
transport outcome differed and the content were identical, it does. The observation is a
function of the transport interaction rather than of the publisher's expressive content,
so **what is appropriated differs in kind and not in degree** -- and the obvious objection
is answered in the record rather than left standing: a status code is information the
publisher produced, and the six activities rule 8 governs ask whether we are appropriating
a publisher's CONTENT OR DATABASE, not who caused a fact to be observable. **A
project-governance distinction, explicitly not a legal conclusion.**

**MODEL A WAS REFUTED ON STRUCTURE RATHER THAN EFFORT**: the evidentiary standard cannot
be met for a target that has never published terms, because there is nothing to retrieve.
**MODEL C WAS REFUTED AS THE WRONG LAYER** -- for such a target the operator would be
reviewing nothing, which reproduces Model A's problem in a form that LOOKS like review
while having no basis, and the part of it that is real is mechanical and survives as
GOV-4's preflight. **MODEL D WAS REFUTED** because the two activities CAN be
distinguished on material the repository already holds.

**PRECEDENCE IS A FUNCTION, NOT A LABEL.** The track is determined by the DECLARED
RETENTION PROFILE and never by the caller's stated intent; source collection wins wherever
both could apply. **And the boundary is structural rather than a note beside it**: the
observation track's own retention contract has no persistable body class, so a
body-retaining configuration **is not expressible in it**. A validator check proves the
structural claim against the contract rather than trusting the sentence.

**GOV-2 IS `R1_RESPECT_DISALLOW`, AND THE FAILURE SEMANTICS WERE READ RATHER THAN
RECALLED.** RFC 9309 was retrieved -- the single external request of a budget of eight --
because writing what a standard says from memory is the error Mission 1.71 avoided by
deferring CIDR blocks to IANA. **Thirteen conditions, one outcome each**, and every row
says whether it follows the standard or is stricter than it. `R0` was refused on the
project's own `source-registry-v1.md` §1 rule 6. **`R2` WAS REFUSED FOR A REASON WORTH
KEEPING**: excluding every target whose robots.txt is merely ABSENT would make the
measured population a function of whether a site publishes one, **a coverage bias WE would
be introducing** in the very arc whose subject is population honesty -- so it is adopted
for the UNREACHABLE cases, where the standard itself requires complete disallow, and
refused for the ABSENT case, where the standard permits access. **401 and 403 exclude and
the record says that is ours**, because a robots.txt refusing an unauthenticated client
contradicts the track's own public-accessibility precondition.

**GOV-3 IS `D2_ALLOWLISTED_HEADERS_AND_STATUS` WITH `BODY_PERSISTENCE_DEFAULT =
DISABLED`**, and the trap it closes is that **not persisting a body is not the same as not
receiving bytes** -- the network read stays bounded whether or not anything is kept. The
secret-bearing header set is **always excluded and a run may not widen the allowlist into
it**, because an allowlist a caller can extend into `Set-Cookie` is not an allowlist. A
`Location` value is transient in raw form and minimized when persisted, with the record
stating that the query component was dropped, so a reader knows the representation is
minimized rather than complete. **Every retention number carries
`decision_kind = PROJECT_POLICY_DEFAULT`.**

**GOV-4 KEEPS MISSION 1.71'S INVARIANT INTACT**: an excluded target is **not removed from
the corpus**, it becomes a terminal accounting record in a `NOT_ATTEMPTED` family.
Deleting it would shrink `N`, which is precisely the defect that closed the external
routes. Unknown terms are `TARGET_TERMS_NOT_INDIVIDUALLY_REVIEWED` -- **neither a
favourable fiction nor an impossible per-item human review**, which would have reinstated
Model C silently as a side effect of a target policy. The preflight is ordered and
first-match-wins, so two runs over one corpus classify identically and give the same
reason.

**GOV-5 CHOSE ACTUAL NUMBERS, AND EVERY ONE SAYS OUT LOUD WHAT IT IS.** Fifteen bounds,
all finite or explicitly `DISABLED`, all carrying `value_source = PROJECT_POLICY_DEFAULT`:
500 targets, global concurrency 4, **per-origin concurrency 1 and one request every five
seconds**, 10 s connect, 20 s read, 5 redirects, **0 retries**, 64 KiB headers, 1 MiB
network read, 2 MiB per target, 6 h run, 1 robots fetch per origin, 6 requests per target,
backoff `DISABLED` rather than absent. **Retries are zero because a retry can observe a
different world state and Mission 1.71 left the which-attempt-counts rule to the
construct**, so a non-zero value would create records under a selection rule that does not
exist. **One target is not one request**: redirects and robots retrievals both count
toward the origin budget.

**NOTHING WAS WEAKENED AND NOTHING WAS AUTHORIZED.** Registered sources 29 before and 29
after, no review touched, no target registered, no eligibility changed. **Twelve
eligibility requirements, none defaulting to approval when unknown**, and a run
additionally needs a specific corpus, request contract, construct and operator approval.
**Common Crawl and HTTP Archive keep Mission 1.70's verdicts verbatim** and the new track
is explicitly recorded as NOT repairing their missingness.

**THE CANDIDATE REGISTRY RULE WAS REVIEWED AGAIN AND STILL NOT ADDED.** Mission 1.71
refused to count its own designed solution as an empirical instance; **writing a policy
that respects a rule is not observing an apparatus fail without it** either. Registry
unchanged at **15**.

**0 target HTTP requests, 0 robots target requests, 0 crawls, 0 browser runs, 0 curl or
wget executions, 0 Common Crawl queries, 0 BigQuery executions, 0 dataset downloads, 0
target-value exposures, 0 accounts, 0 trials, 0 purchases, 0 credential reads, 0 mailbox
searches, 0 enquiries sent**, 0 corpora, 0 exclusion entries, 0 runs, 0 crawlers, 0 sources
registered, 0 canonical mutations, 0 thresholds, 0 Claims, 0 Evidence, 0 independence
groups, 0 reliability values, 0 scores, 0 model calls, 0 embeddings, 0 migrations. 1 of 8
documentation requests. ONYPHE still `NOT_CHECKED_AFTER_DISPATCH`, Netlas still pending,
scanner arc parked, Q1 unchanged, **`PAIR_ANALYSIS_NOT_READY`**.

**Verification.** Validator probed with **186 deliberate violations, 186 caught** (183 by
rule, 3 by drift) plus **7 of 7 positive controls, all variants rather than the shipped
bytes**. **A malformed guard in this mission's own validator was found and removed**: a
conditional expression that would have raised with an empty message had it ever fired,
sitting beside the check that actually does the work -- the guard-that-cannot-speak shape
this repository keeps finding. **101 new tests**; **2532 bare-python tests**; all pytest
suites passed with the database unchanged; **`ruff format --check`, `ruff check` and mypy
all run through `uv` before the PR** per §59; all **42** CI gates.

## 1.106 — 2026-09-06 (Sprint 1 / Mission 1.71)

**`BOUNDED_HTTP_FETCHER_APPARATUS_CONTRACT_READY_DEDICATED_POLICY_REQUIRED`.** The
apparatus semantics close completely. The governance shape does not, and what is missing
is named rather than vague.

**THE APPARATUS CONTRACT CLOSES THE THING MISSION 1.70 COULD NOT BUY EXTERNALLY.** One
terminal accounting record per manifest item per governed run,
`corpus_manifest_count == terminal_target_records_count`, **17 terminal outcomes over 8
missingness classes with a total mapping and no unreachable class**. An item that was
never attempted stays in the population; a retry is a child attempt rather than a new
member; an abort turns every remaining item into `RUN_ABORTED_BEFORE_ATTEMPT` rather than
letting it vanish.

**AND THE DESIGN'S OWN TEMPTATION WAS THE ONE TO WATCH.** An apparatus we control could
reproduce exactly the defect that closed the external pair -- storing only responses --
in a system where nobody else could be blamed for it. That is why missingness is
first-class and why `only_responses_are_stored` is a refusal rather than a preference.

**ONE MISSINGNESS CLASS WAS ADDED BEYOND THE BRIEF'S MINIMUM, AND IT MATTERS**:
`APPARATUS_FAILURE_NOT_A_WORLD_FACT`. An internal fetcher error filed under
`ATTEMPTED_NO_HTTP_RESPONSE` would record that the target did not answer when what
happened is that we broke, and a denominator built on it would absorb our own defects as
the world's silence.

**AND ONE STAGE WAS TAKEN AWAY FROM THE APPARATUS.** `PREDICATE_EVALUABLE` is not
something a fetcher can certify: whether a received response is evaluable depends on what
the predicate needs, and no predicate exists. So the apparatus tops out at
`RESPONSE_RECEIVED` plus what it captured, **`N`, `A` and `R` are computable by the
apparatus while `E` and `P` are explicitly the construct's**, and which classes enter the
denominator is `NOT_CHOSEN_BY_THIS_MISSION`.

**THE DOMINANT GOVERNANCE FINDING IS NOT ANY SINGLE RUBRIC ROW, AND IT WAS LOCATED IN THE
REPOSITORY'S OWN RULES RATHER THAN ASSERTED.** The existing gate governs collection from a
REGISTERED source. Routed through it, a corpus of arbitrary public sites is refused target
by target -- `source-registry-v1.md` §1 rule 1 (*public visibility is not permission*),
rule 2 (*uncertainty is never permission*), rule 8 (a GRANT required for six named
activities, `NOT_ADDRESSED` on any one blocking), and `acquisition-authorization-v1.md` §1
rule 5 (each resource authorised separately). **Not because a publisher objected, but
because nobody asked.** That is the gate working, and **the collapse it forces is the
finding**: restricting the corpus to targets that DO hold a review means restricting it to
the 29 registered sources, which destroys exactly the directability that made the operator
route worth designing.

**THE MECHANISM IS NOT NOVEL AND THE EVIDENCE IS THIS ARC'S OWN BUDGET.** Missions 1.59 to
1.70 performed bounded, identified, one-off HTTP GETs against third parties holding no
source review at all, routinely. **And the distinction that survives it is stated rather
than glossed**: the request is identical and the destination of the RESULT is not -- a
documentation read informs a human judgement, a measurement becomes Evidence under a Claim
at corpus scale.

**WHAT IS RETAINED DECIDES WHICH REGIME APPLIES, WHICH IS WHY DATA MINIMIZATION IS NOT A
SIDE POLICY.** Retaining response bodies retains the publisher's content; retaining a
status line and named headers is closer to a record of our own request. **That is a
DISTINCTION and explicitly not a legal conclusion**, and the bound is written into the
record beside it.

**FIVE NAMED POLICY DECISIONS, NONE SETTLED HERE**: whether this is a governed activity
distinct from source collection and under what track (**ADR-level, and a design mission
inventing a governance shape in passing is the change-control shape `docs/CLAUDE.md`
refuses**); the robots policy, which is architectural rather than a setting because a
robots-respecting apparatus needs a retrieval stage, a terminal outcome and a missingness
class of its own; body capture and the retention regime; the target-exclusion procedure;
and the numeric load bounds, which are **mandatory and deliberately unset**, because no
retrieved document establishes a figure and inventing one is the invented number rule 7
refuses.

**OUTCOME G WAS AVAILABLE AND REFUSED**: no current rule prohibits the architecture, and
**the absence of a shape is not a prohibition** -- reporting one would convert *nobody has
decided* into *the project has refused*. Outcome D was refused too, because target-specific
review is downstream of the shape question rather than the dominant blocker. Outcome A was
refused because five rubric rows genuinely require a decision, and F because the
repository's documents are sufficient to name the gap precisely.

**SELF-OPERATION SUPPLIES DIRECTABILITY AND NEVER INDEPENDENCE**, so
`INDEPENDENCE_ARCHITECTURE_PLAUSIBLE` and never `INDEPENDENT_EVIDENCE_GROUP_READY`, **0
independence groups**, and **two local processes are not two groups** -- they share code,
configuration, vantage, resolver and network path, and counting them twice would
manufacture corroboration out of repetition. **Nine counterpart requirements are frozen and
0 counterparts were evaluated, ranked or selected.** Common Crawl and HTTP Archive keep
Mission 1.70's verdicts verbatim, and **the operator apparatus does not repair their
records retroactively.**

**THE CANDIDATE REGISTRY RULE WAS REVIEWED AND NOT ADDED.** Designing AROUND a failure mode
is not observing a second instance of it -- if it counted, every registry rule could be
promoted by writing a contract that respects it, and the registry would record our
intentions rather than what apparatuses do. **Registry unchanged at 15**, and a validator
check refuses any record that counts this mission's own design as an instance.

**NO EXTERNAL DOCUMENTATION REQUEST WAS SPENT, AND THAT IS A DECISION**: 0 of 12, because
no gate here turns on a quotable sentence, and the one class of external fact the design
needs -- the exact numeric address ranges -- is **deferred to the named IANA registries at
implementation rather than transcribed from recall**, since a governance artifact carrying
recalled CIDR blocks would breach rule 4 and rule 7 at once and a mistyped block is a
silent hole in the guard that exists to prevent one.

**0 target HTTP requests, 0 crawls, 0 browser runs, 0 curl or wget executions, 0 Common
Crawl index queries or data downloads, 0 BigQuery executions, 0 HAR downloads, 0
measurement API executions, 0 target-value exposures, 0 accounts, 0 trials, 0 purchases, 0
credential reads, 0 mailbox searches, 0 enquiries sent**, 0 sources registered, 0 governance
or canonical mutations, 0 corpora created, 0 runs executed, 0 crawlers implemented, 0
thresholds, 0 Claims, 0 Evidence, 0 independence groups, 0 reliability values, 0 scores, 0
model calls, 0 embeddings, 0 migrations. ONYPHE still `NOT_CHECKED_AFTER_DISPATCH`, Netlas
still pending, scanner arc parked, Q1 unchanged, **`PAIR_ANALYSIS_NOT_READY`**.

**Verification.** Validator probed with **224 deliberate violations, 224 caught** (221 by
rule, 3 by drift) plus **6 of 6 positive controls**, and the controls are VARIANTS rather
than the shipped bytes -- a governance-feasible-but-unauthorized apparatus, a blocked
outcome named on a rule, **a terminal taxonomy with every outcome renamed and the invariant
intact**, a corpus with approved query strings, a run manifest carrying an image digest, and
an unresolved independence architecture. The renamed-taxonomy control is the one that
matters: it proves the validator checks the property rather than my prose. **120 new
tests**; **2431 bare-python tests**; all pytest suites passed with the database unchanged;
**`ruff format --check` and `ruff check` both run before the PR**, after Mission 1.70
shipped a formatting failure to CI; all **41** CI gates.

## 1.105 — 2026-09-06 (Sprint 1 / Mission 1.70)

**`FIXED_CORPUS_WEB_REQUIRES_OPERATOR_CONTROLLED_ROUTE`.** Q1 entered this mission with
what no earlier class in the arc had held at once — two independently established
producers, dated artifacts on both sides, raw headers on one, and coverage published
rather than hidden. It leaves with **the coverage published and its SEMANTICS
undocumented on both sides simultaneously**, which is the finding.

**NEITHER ROUTE SAYS WHETHER A URL THAT WAS ATTEMPTED AND FAILED APPEARS IN WHAT IT
PUBLISHES**, and both were checked on their own pages rather than reasoned about. Common
Crawl's index defines `status` as *"the HTTP status code returned when fetching the
page"* and its columnar schema carries `fetch_status` — *"HTTP response status code"* —
`fetch_redirect` and a `content_truncated` field taking `length`, `time`, `disconnect`
and `unspecified`; nothing on either page says whether a URL fetched unsuccessfully, or
never captured at all, has a row. HTTP Archive's pages table is **one row per page
TESTED and carries no failure column**; the attempt-level facts that exist — `retry_count`,
`tested_url`, `visited` — sit inside a metadata blob and none of them is a test status.

**THAT IS NOT THE HIDDEN-FRAME PROBLEM IN A NEW PLACE, AND THE DIFFERENCE IS WHY IT
BLOCKS.** A hidden frame means you cannot say which items were eligible. This means you
cannot say whether an item's **ABSENCE** is a fact about the world or a fact about the
apparatus — so a joint population over a frozen corpus would carry a denominator neither
publisher can describe, and every proposition resting on it would inherit that.

**FIVE POPULATION STRATEGIES WERE EVALUATED AND ALL FIVE REJECTED**, including the two
that would have kept the route alive. Provider-native intersection fails because neither
apparatus can be pointed at a corpus. Planned-target and attempted co-coverage each need
a set neither publishes. **Realized successful co-coverage was refused outright**: it
selects the population on the measurement's own outcome, and a rule written before
retrieval is preregistered only if what it selects on is DEFINED — **temporal ordering
is necessary and never sufficient**, which is the reusable half of this mission.
Missingness-preserving was taken seriously and still needs the missingness to be legible,
which is the fact that is missing.

**THE DECISION IS `EXTERNALLY_FROZEN_POPULATION_REQUIRES_OPERATOR_FETCHER`, AND TWO
STRONGER READINGS WERE REFUSED IN OPPOSITE DIRECTIONS.** Calling the architecture
INVALID would assert that coverage IS success-conditioned, which no retrieved page
establishes — **undocumented is not established-as-outcome-dependent**. Calling it
UNRESOLVED would understate a question that did close in one direction: an operator-run
fetcher supplies directability and legible missingness by construction, which is exactly
what both external routes lack.

**THE REQUEST CONTRACT WAS TABULATED BEFORE ANY VERDICT WAS ISSUED**: fifteen fields, **4
DIFFERENT_AND_LOAD_BEARING, 11 UNKNOWN, 0 MATCHABLE**, so
`REQUEST_CONTRACT_COMPATIBILITY_NOT_ESTABLISHED` and the shared world-state family is
recorded as PLAUSIBLE_CONDITIONAL rather than asserted. **A browser page load is not a
crawler fetch**, and HTTP Archive's own `is_main_document` — *"the first HTML request
after redirects"* — means the row is not the response to the requested URL, so **no
redirect predicate binding was chosen here**, because that choice belongs to a construct
nobody has frozen.

**RIGHTS ARE FEASIBILITY AND WERE NOT TURNED INTO APPROVAL.** Common Crawl's terms say
*"CC strongly recommends that you obtain the advice of legal counsel before making any
use, including commercial use"* — **a recommendation to seek advice is not a grant** —
so `ROUTE_RIGHTS_REVIEW_REQUIRED`; HTTP Archive's licence is absent from its FAQ and its
homepage, so `UNKNOWN` rather than a guess in either direction. **0 sources registered,
0 governance mutated, 0 approvals.**

**THE OPERATOR ROUTE IS AN ARCHITECTURE AND NOTHING RAN.** `REQUIRES_DEDICATED_REVIEW`
with the conditions a future review would have to settle written down;
`INDEPENDENCE_ARCHITECTURE_PLAUSIBLE` and **explicitly not independent because we would
run it**; implemented **false**, crawled **false**, HTTP measurement requests **0**.

**Q1 STAYS `PROMISING_BUT_ROUTE_QUALIFICATION_REQUIRED`, UNCHANGED**, no class is
selected, and **`selected-quantity-class-v1.json` does not exist** — §41 makes the
artifact conditional on strategic viability, and the validator refuses its existence.
**No construct was frozen and no predicate chosen.** A candidate rule,
`COVERAGE_SEMANTICS_MUST_DISTINGUISH_ATTEMPT_FROM_SUCCESS`, was **offered and NOT added**
under the standard Mission 1.67 set for itself — one shape seen twice on two routes is
one instance, not two — so the **registry is unchanged at 15**.

**Mission 1.69's decision record was not edited**, and the validator refuses any record
claiming it was.

**Held evidence again did most of the work**: 11 of 20 first-party requests, 4 navigation
searches, **0 failed**. **0 target-value exposures, 0 crawls, 0 target HTTP requests, 0
Common Crawl index queries, 0 WARC/WAT/WET downloads, 0 BigQuery executions, 0 HAR
downloads, 0 API executions, 0 dataset downloads, 0 trials, 0 purchases, 0 accounts, 0
credential reads, 0 mailbox searches, 0 enquiries sent**, 0 sources registered, 0
governance or canonical mutations, 0 thresholds, 0 Claims, 0 Evidence, 0 independence
groups, 0 reliability values, 0 scores, 0 model calls, 0 embeddings, 0 migrations, 0
crawlers implemented. ONYPHE stays `NOT_CHECKED_AFTER_DISPATCH`, Netlas stays unresolved
with nothing decoded or guessed, the scanner arc stays parked, **`PAIR_ANALYSIS_NOT_READY`**.

**Verification.** Validator probed with **136 deliberate violations, 136 caught** (133 by
rule, 3 by drift) plus **5 of 5 positive controls** — an unresolved population, a valid
pre-value co-coverage architecture, a valid missingness-preserving one, a strategically
viable Q1 selected with its artifact and no construct, and an alternative no-selection
outcome — with the fourth checked to be discriminating rather than vacuous. **§23 met for
the eleventh time** and repaired structurally: a guard refusing any number under a
reliability-named key fired on `reliability_assessments`, a database row count, and the
repair scopes the guard to three NAMED census blocks whose reliability-named entries are
all covered by the hard-zero loop — never a loosening of what it compares. Five ruff
findings fixed **by hand**, the SIM102 collapse included, and the probe re-run afterwards.
One tautological test of my own — a no-op `.replace()` guarding a substring — was replaced
with a structural check over the pages table's actual columns. **104 new tests**; **2311
bare-python tests**; all pytest suites passed with the database unchanged across 29 tenant
tables and the baseline re-measured identical afterwards; all **40** CI gates.

## 1.104 — 2026-09-06 (Sprint 1 / Mission 1.69)

**`FIXED_CORPUS_WEB_MEASUREMENT_PROMISING_BUT_ROUTE_QUALIFICATION_REQUIRED`.** Eight
quantity classes evaluated outside the scanner class, and **five of them have exactly
ONE party positioned to produce the quantity while a sixth has none of its own.** Every
other publisher is a distribution layer.

**THAT IS MISSIONS 1.46 AND 1.57's LAW RECURRING IN FIVE DOMAINS IT HAD NEVER BEEN
TESTED IN**, and each one was confirmed on the aggregator's or the registry's own words
rather than reasoned about:

| class | what the producer's own documentation says |
|---|---|
| package downloads | *"This table is populated through the Linehaul project by streaming download logs from PyPI to BigQuery."* |
| code activity | *"Activity archives for dates starting 1/1/2015 are recorded from the Events API"*, *"as reported by the GitHub API"* |
| publication activity | *"We don't index journals directly — we harvest Crossref and friends"* |
| procurement | one submitted notice, many publishers (held evidence, Missions 1.15.x) |
| public attention | each metric produced by exactly the platform that logged it (held evidence, Missions 1.19 and 1.47) |

**THE EXCEPTIONS ARE THE THREE CLASSES NOBODY IS POSITIONED TO PUBLISH
AUTHORITATIVELY**: what services answer on the internet, what a web server returns for a
defined request, and what a resolver receives for a defined query. Each must be
established by asking, which is exactly the condition Mission 1.58 identified. The first
of the three is the scanner class, parked for a different reason — it has two producers
and no construct they can both witness.

**Q1 IS THE FIRST CLASS IN THIS ARC WITH TWO ESTABLISHED INDEPENDENT PRODUCERS.** Common
Crawl fetches pages with its own crawler — *"CCBot identifies itself in its `UserAgent`
string as: CCBot/2.0"*, on *"dedicated IP address ranges with reverse DNS"* — and stores
*"the raw response ... but also the HTTP header information"* in dated crawl releases.
HTTP Archive loads each page itself through *"a private instance of WebPageTest with
private test agents, which are the actual browsers that test each web page"*, publishes
*"one row per page tested"* with its crawl date, and documents its request contract down
to the user agent, the viewport and *"Google Cloud Platform locations based in the
USA"*. **§36 demanded first-party evidence on both sides rather than an inference from
the organisations differing, and this is it.**

**AND THE FIXED-CORPUS ADVANTAGE IS ONLY HALF DELIVERED, WHICH IS THE FINDING.** §6
hoped a frozen corpus would replace each provider's hidden discovery frame. What is
delivered is that **coverage is INSPECTABLE**, which no scanner offered. What is not is
that **neither apparatus can be POINTED at a corpus**: Common Crawl selects its own URLs
and states plainly that *"Common Crawl's dataset is a sample of the web, and we do not
generally archive any entire website but a randomly selected subset of it"*, while HTTP
Archive's list comes from the Chrome UX Report. So a joint population over a frozen
corpus C is C intersected with two independently determined coverages. **Coverage is
metadata rather than a measurement value and both publish it, so a restriction rule
could in principle be frozen before any value is retrieved** — and whether that is an
honest preregistration or a population chosen after looking is the one load-bearing
question this mission leaves open.

**NOTHING WAS SELECTED, AND OUTCOME B WAS AVAILABLE.** §50's outcome I explicitly does
not select the class, and selecting Q1 on the expectation that the population question
resolves would preregister an experiment on an architecture nobody has established.
**§35's tie-break preference for Q1 was NOT exercised**, because it is a tie-break and
may not push a class through a failed gate.

**OUTCOME H WAS ALSO REFUSED, IN THE OTHER DIRECTION.** H says no class has two credible
independent routes. Q1 HAS two, established first-party on both sides; what is
unresolved is population alignment. Reporting H would have understated what was
established and sent the next mission hunting routes it already has.

**A DISTINCTION HAD TO BE MADE MACHINE-CHECKABLE MID-MISSION, AND THE VALIDATOR IS WHAT
FORCED IT.** Its first version counted own-measurement routes as producers, and refused
the record for public attention: Wikimedia and a search engine both measure their own
events perfectly, and **a search is not a content request**. The fix was a per-route
field recording whether a route produces THIS class's world-state unit, which turns §20
from a sentence into a check. Under it, five classes have one producer, one has none,
and three have two.

**THE MISSION 1.68 CANDIDATE RULE WAS EXAMINED AND NOT ADOPTED.** Three possible second
instances were checked and each is better described by a rule the registry already has —
`SOURCE_EXCLUSIVE_METRIC` for the registry case, and the mirror trap for the two
aggregators. The standard applied is the one Mission 1.67 set for itself when it adopted
the previous candidate: a second independent instance **in a different shape**.
**Registry unchanged at 15.**

**THE SCANNER ARC IS PARKED, NOT REFUTED**, and its reopening conditions are written
down: an ONYPHE reply, the Netlas operational questions closing, or a positive
first-party answer to Mission 1.68's one-sentence question. §1 required that and the
validator enforces it.

**HELD EVIDENCE DID MOST OF THE WORK.** Seven repository findings were reused without
re-retrieval, and new requests were spent only where a class-specific question had no
recorded answer. 14 of 24 first-party requests, 4 navigation searches, 8 serious classes
of 8 with a ninth deliberately not invented, and **0 requests spent reopening the scanner
class against a cap of 2**.

**0 measurement values, 0 crawls, 0 HTTP measurement requests, 0 dataset downloads, 0
BigQuery executions, 0 API executions, 0 package, repository, publication, procurement,
trend or DNS queries, 0 trials, 0 accounts, 0 credential reads, 0 mailbox searches, 0
enquiries sent.** 0 sources registered, 0 source reviews mutated, 0 governance
mutations, 0 canonical mutations, 0 thresholds, 0 Claims, 0 Evidence, 0 reliability
values, 0 model calls, 0 embeddings, no migration, no construct frozen, no pair
selected. ONYPHE stays `NOT_CHECKED_AFTER_DISPATCH` and Netlas unresolved.
**`PAIR_ANALYSIS_NOT_READY`.** Validator probed with **127 deliberate violations, 127
caught** — 124 by rule, 3 by drift — plus **4 of 4 positive controls**, including a
complementary-only class, a two-producer viable class, a properly evidenced selection
with its artifact, and an alternative no-selection outcome. **§23 for the tenth time**: a
guard compared a field to the literal `"NO"` and refused a value reading *"NO. Neither
can be pointed at a corpus we choose."* — repaired by splitting the verdict into a
boolean rather than loosening the comparison. **56 new tests**, **2207 bare-python
tests**, all pytest suites passed with the database unchanged, and all **39** CI gates.

## 1.103 — 2026-09-06 (Sprint 1 / Mission 1.68)

**`NO_PRODUCT_RELEVANT_CONSTRUCT_WITH_TWO_ROUTES_IDENTIFIED`.** Five constructs
evaluated against seven apparatuses, and **every one has exactly ONE plausible route
— a DIFFERENT apparatus each time.** That pattern is the mission's output, and it is
visible only because five constructs were compared rather than one pursued.

| construct | its one route |
|---|---|
| SSH identification (control) | Netlas |
| TCP/22 SYN responsiveness | Rapid7 Project Sonar (`sonar.tcp`) |
| HTTP response to an IP-addressed GET | Rapid7 Project Sonar (HTTP study) |
| TLS certificate observation | Rapid7 Project Sonar (certificate studies) |
| DNS record configuration | Rapid7 Project Sonar (FDNS/RDNS) |

**THE APPARATUSES ARE INDIVIDUALLY CAPABLE AND PAIRWISE DISJOINT.** They are not
failing to measure; they are failing to measure THE SAME THING as each other, on the
same population, with the same temporal object. **And there is a reason, which is
about what these products sell**: a commercial scanner publishes SERVICES, because
that is what its customers buy, and a service record presupposes a response. The
discovery stage — which port answered — is an internal step they do not publish as a
separately addressable artifact. Sonar publishes it because `sonar.tcp` is a research
dataset rather than a search product.

**THE PIVOT WAS ALLOWED AND IS NOT A RELAXATION.** The SSH identification predicate
is not something this product promises anybody; it was chosen to prove that two
independently produced observations can witness one source-independent proposition.
The control was evaluated through the same matrix rather than exempted, and its status
stays **`NO_TWO_QUALIFIED_APPARATUS_ROUTE_IDENTIFIED`** — never FAILED, BAD_CONSTRUCT
or INVALID. Its problem is reachability under the apparatus market as documented.

**C1 CAME CLOSEST AND WAS NOT SELECTED, WHICH IS THE WHOLE OF §30.** `sonar.tcp`
publishes *"regular snapshots of the responses to zmap probes against common TCP
services"* as dated immutable per-port files — `2026-09-05-1788609721-tcp_dns_53.csv.gz`
— so a file is selected **by port and by date before any value is retrieved**. That is
the strongest single route the arc has produced. Its second route is UNRESOLVED rather
than blocked on two apparatuses, and **selecting on the expectation that the missing
sentence exists would preregister an experiment on a route nobody has established.**

**THE DECISIVE UNRESOLVED QUESTION IS ONE SENTENCE WIDE**: does any apparatus publish,
as a separately addressable artifact, a record that a port ACCEPTED A TCP CONNECTION
WITHOUT PRODUCING AN APPLICATION RESPONSE? Netlas's collection is named Responses, its
documented fallback field stores *"the unparsed network response"* — which presupposes
the peer sent something — and no retrieved page says whether a document exists
otherwise. If it does not, Netlas counts a strict subset and the same-proposition gate
fails.

**A SYN RESPONSE IS NEVER AN SSH SERVER**, and the validator enforces it structurally
as well as lexically: a SYN predicate may not carry an SSH subject, must state why the
two differ, and must refuse the reading in its explicit non-claims. A SYN response is a
transport-layer fact produced by the TCP stack; the whole content of RFC 4253 §4.2's
discriminator is absent from it.

**BLOCKERS ARE NOW CLASSIFIED GLOBAL OR CONSTRUCT-SPECIFIC, AND IT MATTERS IN BOTH
DIRECTIONS.** Sonar's Mission 1.67 rejection was construct-specific and **correctly
disappears** under a predicate that reads no response bytes — carrying it forward would
have repeated Mission 1.67's answer without repeating its work. Shodan's and LeakIX's
temporal architectures and Shadowserver's per-requester frame are **global and survive
every construct**, because no change of predicate repairs where a timestamp points.
And a construct-specific blocker **appeared** where it had never applied: on ports 80
and 443 Netlas queries *"not only by IP address but also by domain names"*, limits
*"the number of virtual sites per IP to 100,000"*, and saves *"each response as a
separate document"* across redirects — with the Host header it sends undocumented. On
every other port it sends requests by IP address without domain names.

**CENSYS WAS RE-EXAMINED RESOURCE BY RESOURCE AND THE SUMMARY GUARD FIRED A THIRD
TIME.** A search summary reported that Censys *publishes an updated daily snapshot of
the state of the public address space*; the Platform historical-data page says instead
that *"Every time that Censys performs a scan against a host, Censys preserves a
snapshot of that host during that point in time"*, reached through Service History and
Scan History tabs **after a host is found**. Its host dataset documents
`host.services.scan_time` as *"When the service was last observed by a Censys scan"* —
**the exact temporal object Missions 1.58 and 1.59 rejected, re-confirmed on current
documentation rather than carried over from a report.** This is the first time the
guard has fired on a summary that was FAVOURABLE to a candidate, which is the direction
that matters. **The Universal Internet Dataset is genuinely different** — dated
immutable snapshots addressed by a date-based ID, the second such artifact in this arc
alongside Sonar — and stays UNRESOLVED because raw banners are not mentioned, the
schema is directed to a page inside the authenticated console, and its contents are
described as *"enriched with third-party data"*, an open-ended clause
`ENUMERATED_EXCEPTIONS_MAKE_A_LINEAGE_CLAIM_CHECKABLE` refuses.

**OUTCOME F WAS AVAILABLE AND REFUSED.** F asserts the apparatus class itself is the
dominant limitation. The evidence points that way and does not establish it: several
cells are UNRESOLVED rather than BLOCKED, and reporting F would convert *this mission
could not establish it* into *it cannot be done* — the conversion this repository has
refused since Mission 1.60.

**HELD EVIDENCE PAID FOR ITSELF, MEASURABLY.** Eleven retrievals answered a
seven-apparatus, five-construct matrix; Mission 1.67 spent twenty-four on two
apparatuses. The difference is the records already in the repository, and this mission
was partly a test of whether accumulated apparatus knowledge reduces research cost.

**A REUSABLE RULE WAS OFFERED AND NOT ADDED**, under the standard Mission 1.67 itself
set: `A_PUBLISHED_SURFACE_IS_THE_SALEABLE_OBSERVATION_NOT_THE_MEASUREMENT_PIPELINE` has
one shape so far, and the frame-uniformity rule was adopted only when a second
independent instance appeared. **Registry unchanged at 15.**

11 of 18 first-party requests, 3 navigation searches, 5 serious constructs of 6, and a
sixth deliberately not invented. **0 measurement values retrieved, 0 target-value
exposures, 0 API executions, 0 dataset downloads, 0 counts, 0 hosts, 0 banners, 0
trials, 0 accounts, 0 credential reads, 0 mailbox searches, 0 enquiries sent**, 0
sources registered, 0 governance mutations, 0 canonical mutations, 0 thresholds, 0
Claims, 0 Evidence, 0 reliability values, 0 model calls, 0 embeddings, no migration.
ONYPHE stays `NOT_CHECKED_AFTER_DISPATCH`, Netlas unresolved with nothing decoded.
**Qualified apparatuses 0, `PAIR_ANALYSIS_NOT_READY`, no pair selected or compared.**
Validator probed with **109 deliberate violations, 109 caught** — 106 by rule, 3 by
drift — plus **4 of 4 positive controls**, including a two-route viable construct, a
properly evidenced selection with its artifact, and an alternative no-selection
outcome. **62 new tests**, **2151 bare-python tests**, all pytest suites passed with
the database unchanged, and all **38** CI gates.

## 1.102 — 2026-09-06 (Sprint 1 / Mission 1.67)

**`NO_NEW_QUALIFYING_APPARATUS_IDENTIFIED_WITHIN_BOUNDED_SEARCH`.** Two apparatuses
nobody in this arc had evaluated were taken to complete packages, and they failed at
two different gates — which is worth more than either failure alone, because they
are **the two halves of one conjunction, seen separately and never together**.

**RAPID7 PROJECT SONAR HAS THE TEMPORAL OBJECT EVERY EARLIER CANDIDATE LACKED, AND
CANNOT CARRY THE PREDICATE.** Its studies publish individually named, individually
addressed files — `2018-06-15-1529049662-fdns_aaaa.json.gz`, reached at
`.../opendata/studies/{study_id}/{filename}/` and listed per study in
`sonarfile_set` — so an artifact is selected BEFORE any measurement value is
retrieved. That is §13's own PASS example, and Missions 1.59, 1.62 and 1.66.2 all
failed to find it. **A2 is still PARTIAL rather than PASS**, because no retrieved
document defines what the date in a filename DENOTES, and a window maps onto an
artifact only if its date is defined. What kills it is A3: the retrievable catalogue
is eight datasets, the only one covering arbitrary TCP ports is *"SYN scan results
for common TCP services across all of IPv4"*, and its own wiki says the output
*"contains the IP addresses that responded positively to the SYN for the port in
question."* **A SYN response says a port answered and carries not one byte the peer
sent.** The apparatus states first-party that *"TCP studies include SSH, SMB, Telnet,
RDP, Mongo, Redis, CouchDB, and more"* — so **the identification string is MEASURED
and is not in the published retrievable catalogue**, which is
`THE_RETRIEVABLE_FRAME_IS_NOT_THE_MEASURED_FRAME` recurring as a catalogue-content
restriction where Mission 1.62 met it as a per-requester one. **This does not
establish that Sonar cannot capture raw responses** — its HTTP datasets plainly do —
and §16 forbids transferring their semantics to a TCP/22 resource.

**SHODAN PUBLISHES THE OTHER HALF.** Own crawling is stated plainly: *"the crawlers
work 24/7 and update the database in real-time"*, *"Generate a random IPv4 address"*,
*"The algorithm is designed to randomly crawl the Internet once a week."* **A2 FAILS
on three independent first-party facts**, and the middle one is the one that makes
this a finding rather than an unexamined silence: **the Filter Reference was fetched
precisely to check, and documents no time or date filter at all**, so a search cannot
be restricted to a past window. The only historical surface is per-address — *"The
historical IP lookups feature of the API provides data going back up to 90 days"*,
*"it returns at most 1,000 banners"* — and **a per-address history requires already
holding the address**, so obtaining the set for a window means searching a
real-time-updated database and inspecting timestamps afterwards. That is
retrieve-then-inspect, which Mission 1.59 rejected on a different apparatus for the
same reason. **The honest answer is two-level and both halves are recorded**: at
ADDRESS level the history parameter really does look like versioned observation
history; at FRAME level, which is what a count of distinct addresses needs, the
object is a maintained current state.

**SHODAN TRENDS WAS EVALUATED SEPARATELY RATHER THAN FAILED BY INHERITANCE**, because
§16 makes that a rule. Three reasons, any one sufficient: no date-range parameter is
documented, the response carries counts and no identification string, and **the
documentation does not state what the count counts** — so an undocumented count unit
cannot witness a construct that requires DISTINCT IPv4 and forbids row, service-row
and banner counts. **It was not executed**, and both Shodan endpoints are recorded
`SECRET_BEARING_AND_MEASUREMENT_BEARING_DO_NOT_EXECUTE`, carrying Mission 1.66.2's
User API lesson forward to a case where both failures land at once.

**THE FRAME-UNIFORMITY RULE IS ADOPTED, AND ON A SECOND INDEPENDENT INSTANCE.**
Mission 1.66.2 offered `APPARATUS_CONFIGURATION_MUST_BE_UNIFORM_ACROSS_THE_FRAME` and
declined to add it in passing. This mission found a second instance in a **different
shape**: ONYPHE partitions by region (*"same list of 500 ports"* against *"TOP 25
ports"*), Shodan randomises (*"Generate a random port to test from the list of ports
that Shodan understands"* with *"crawling is performed completely random"*). **A rule
demonstrated once looks like a rule about one provider's habits**; two shapes show it
is about whether an apparatus publishes enough structure to say which configuration
reached which part of the frame, however the heterogeneity arose. Distinct from
sampling, which asks which ELIGIBLE targets were attempted where this asks whether
the predicate was eligible at all; from the retrievable frame, which asks what a
REQUESTER may retrieve where this asks what the apparatus MEASURED; and from
time-addressability, which asks WHEN where this asks WHERE. **Registry 14 to 15**,
produced BEFORE final candidate selection, no existing requirement renamed or merged,
and **no historical verdict edited** — §45 honoured, with a Mission 1.62 test
re-pointed from 14 to 15 exactly as Mission 1.63 re-pointed it from 13.

**FOUR HITS DIED AT THE DOCUMENTATION PRE-GATE, AND THAT IS REPORTED APART FROM THE
EPISTEMICS.** BinaryEdge's documentation host 301-redirects every path to one
Coalition customer notice that itself returns 403; ZoomEye failed on all three of its
documented hosts; Criminal IP returned 403 twice; FOFA served a client-side
navigation shell twice. **None became a serious candidate**, and each records what
that does NOT establish — a fact about this mission's reach, in the shape Mission
1.60 recorded for three candidates that later documented fully. **Outcome J was
available and refused**: documentation is numerically the largest group, and reporting
it as THE binding limitation would misdescribe the two candidates that documented
themselves thoroughly and failed on epistemics.

**THE RETRIEVAL-SUMMARY GUARD FIRED TWICE.** A search summary reported BinaryEdge
scanning-engine internals and six months of host history, and another reported
Criminal IP field-level detail with an example timestamp. **Neither exists at the
addresses the live hosts serve**, and nothing from either was used in either
direction. Mission 1.63's nonexistent sentence remains the canonical negative
control, and this is the first mission to meet it twice.

**24 of 36 first-party document requests**, 12 carrying load-bearing content, 4
returning nothing usable and **8 failing outright — all counted**, because a budget
that only counts successes is not a budget. 12 navigation searches, used only to
locate exact first-party paths so a guessed 404 would not spend budget. **2 serious
candidates of a permitted 6.** **0 research data requests, 0 API executions, 0
measurement executions, 0 count-endpoint executions, 0 hosts, 0 banners, 0 downloads,
0 trials, 0 purchases, 0 accounts, 0 credential reads, 0 mailbox searches, 0 enquiries
sent.** 0 sources registered, 0 governance reviews, 0 canonical mutations, 0
reliability values, 0 independence groups, 0 model calls, 0 embeddings, no migration.
ONYPHE stays `NOT_CHECKED_AFTER_DISPATCH` and Netlas stays unresolved with nothing
decoded or guessed. **Total apparatuses 6, qualified 0, so `PAIR_ANALYSIS_NOT_READY`
and no pair selected or ranked.** Validator probed with **119 deliberate violations,
119 caught** — 115 by rule, 4 by drift, the four being exactly the hand-edited
generated pages — plus **4 of 4 positive controls**, including a fully evidenced
qualified package, a two-qualified readiness state that still selects no pair, and a
valid DECLINE leaving the registry at 14. **Two probe defects were found and fixed**:
mutators that returned a sub-record instead of the root, and a restore set that
omitted a file a case mutated, which left Mission 1.66.2's ONYPHE package edited on
disk until the positive controls refused to pass. **One case ESCAPED and the rule was
added rather than the record loosened** — an append-model discriminator beside a
maintained-state temporal object was only refused on the PASS branch, so the
contradiction could sit in a record whose gate read FAIL. **2089 bare-python tests**
run before commit, and all **37** CI gates.

## 1.101 — 2026-09-05 (Sprint 1 / Mission 1.66.2)

**`ONYPHE_PUBLIC_DOCUMENTATION_RECONCILED_RESIDUALS_REMAIN`.** Twelve first-party
documents retrieved and re-read verbatim against the three residual questions.
**No gate moved**, and establishing that is the result.

**THE REUSABLE FINDING IS WHAT A SPENT BUDGET BUYS WHEN IT CHANGES NOTHING.** A
documentation budget that returns no gate change is not a failed budget: it buys
**the difference between an unanswered question and an unpublished answer.** An
unanswered question might be closed by reading more. An unpublished answer can
only be closed by asking, by measuring, or by choosing a different apparatus.
Knowing which of those you face decides the next mission, and this one decides it:
for ONYPHE, further public reading is exhausted.

**FOUR TRUE STATEMENTS THAT DO NOT CLOSE B2, AND ASSEMBLING THEM WAS THE
TEMPTATION.** The category keeps seven months of history. `-hourago` is described
verbatim as *"Query data collected some hours ago"*. The default sort is *"By
default, latest result is displayed first on output"*. And `-sort:0` reaches an
older result. Each is documented, each sounds like an append store, and **each is
equally true of a maintained store**: a record whose timestamp advanced into a
past hour also matches a query over that hour, and a default ordering presupposes
several results without saying whether two can describe the SAME service at two
times. **The page most likely to settle it was fetched for exactly that reason** —
the write-up whose title names historical queries — and it states nothing about
whether a repeated scan creates a document or updates one. **B2 stays PARTIAL, on
a directed search rather than on documents read for other purposes.**

**THE TIMESTAMP SENTENCE IS STILL BOTH THINGS AT ONCE**, quoted verbatim from the
data model: *"timestamp of when the data was collected. Allows tracking when a
given service or vulnerability was last observed."* One sentence, two temporal
objects. Mission 1.62 recorded the ambiguity; this mission confirms it rather than
resolving it in the direction that would keep the candidate alive.

**A GENUINELY NEW CONFIGURATION FACT: THE DATASCAN PORT SET IS REGION-DEPENDENT.**
The same table gives US/FR *"same list of 500 ports"* and SG/CN *"TOP 25 ports"*.
**One apparatus applies at least two configurations to different parts of its own
population.** If port 22 sits inside the 500 and outside the TOP 25, an address
reached only by the SG/CN rotation is not eligible to appear at all, and a count
would mix two populations selected under two different rules — **with the
difference living inside the apparatus rather than between apparatuses.** Recorded
as a named risk rather than a defect, because whether 22 is in either list is
exactly what nobody has published.

**AND THE CONFIGURATION IS NOW DOCUMENTED AS HAVING MOVED.** From the official
retrospective, verbatim: *"From 200+ ports scanned to more than 400 ports"*,
*"Bi-monthly refresh rate from FR and US countries, instead of once per month
previously"*, *"More scanning from HK and SG locations (86 ports for SG & 42 for
HK)"*, *"Number of scanned ports: from 200+ to 1300+ per month"*. Port counts,
cadence, scanner regions and category coverage all changed. **This makes
`APPARATUS_CONFIGURATION_MUST_BE_TIME_ADDRESSABLE` demonstrated rather than
anticipated** — and it makes B4 harder, not easier: before, the port set was
undated and might have been constant; it is now known to move, and its value at a
past window is published nowhere. **The retrospective names HK and SG while the
current page names SG and CN. That is drift, not contradiction**, and reading two
documents about different moments as a conflict would be the error.

**TCP/22 STAYS UNKNOWN AND THE CATEGORY TRANSFER WAS REFUSED AGAIN.** The
published port list carries exactly one section, headed for **ctiscan**, and port
22 appears under it. There is no datascan TCP section. A configuration fact
published for one resource does not establish it for another, and the absence of a
section is not a statement that datascan scans no TCP ports.

**THE USER API LOOKED LIKE A SAFE CONFIGURATION ROUTE AND IS NOT.** Its own
documentation says it lets you *"View name, API key, remaining credit count,
expiry date"* alongside *"List of scanned ports, both TCP & UDP"*. So it is
`SECRET_BEARING_DO_NOT_EXECUTE`: **avoiding measurement contamination is one
property and not exposing a credential is a different one, and the second is not
implied by the first.** It was **not executed**, and no credential was read to
check whether the documentation was loose. **And it would not have answered the
question anyway**: the port list carries no category or region mapping, and this
mission established that the set differs by both — so a generic *scanned ports*
list cannot be attributed to datascan. **Two independent reasons, either of which
alone stops the call.**

**RETENTION IS UNCHANGED AND ITS SILENCE IS RECORDED AS SILENCE.** Verbatim: *"For
data older than 30 days, we remove some fields as they are less useful, and we
truncate data field to 4KB."* The sentence **names the field it truncates and does
not name the fields it removes.** So `data` truncation is not removal and B3 is
not reopened, while the address, the observation timestamp and the scanner node
fields stay **UNKNOWN in both directions** — the archive being useless without
addresses is an argument from what a sensible provider would do, and historical
querying existing proves records are reachable rather than which fields they still
carry.

**A SUPPORT CHANNEL IS ESTABLISHED, CITED RATHER THAN INFERRED**, from the
official blog: *"Do you have any questions? Contact us at support[at]onyphe{dot}io"*,
three times on the page. **Mission 1.65 is not rewritten**: it recorded that the
pages IT inspected published no dedicated support route, which was accurate then
and is still a true statement about that moment. The enquiry is **not resent**, no
second envelope exists, and the one send stands. The address is recorded **as
printed**, not normalised into a usable mailbox, because nothing is being sent and
the record is more useful holding what the page actually shows.

**A CANDIDATE REGISTRY REQUIREMENT WAS OFFERED AND DELIBERATELY NOT ADDED.**
`APPARATUS_CONFIGURATION_MUST_BE_UNIFORM_ACROSS_THE_FRAME` is distinct —
`SAMPLING_IS_LOAD_BEARING` compares population definitions BETWEEN apparatuses,
and the time-addressability rule governs WHEN a configuration applied, while
neither governs heterogeneity WITHIN one apparatus at one time. It is recorded
with its justification for a mission that has the registry in scope, because **a
documentation-reconciliation mission editing a frozen apparatus contract in
passing is the change-control shape §Change control refuses.** Registry unchanged
at **14**.

**THE VALIDATOR REFUSED THIS MISSION'S OWN RECORD, AND IT WAS A FALSE POSITIVE.**
A guard checking that Mission 1.65's statement survives was written against a
phrase in the RENDERED prose, and the page renders it as *What it is not:* rather
than *not a dedicated*. The record was intact. Re-anchored to the record's own
field and to the sentence whose deletion would BE the rewrite — `testing-strategy.md`
§23 for the eighth time, and fixed structurally rather than loosened.

Outcome **C** and not **B**: the closest candidate for a definitively closed
question is configuration mutability, and **establishing that a configuration
CHANGES moves no gate toward PASS.** Reporting B would let that read as progress
toward qualification when it is the opposite.

12 of 12 first-party document requests, one of which 404'd on a guessed path and
is counted anyway. **0 API executions of any kind, 0 credentials read, 0 mailbox
searches, 0 enquiries sent, 0 follow-ups, 0 measurement queries, 0 counts, 0 host
records, 0 banners, 0 trials, 0 purchases.** 0 canonical mutations, 0 sources
registered, 0 governance reviews, 0 reliability values, 0 independence groups, 0
pairs selected, 0 model calls, 0 embeddings, no migration. ONYPHE stays
`INDIVIDUALLY_UNRESOLVED`, **qualified apparatuses 0 of 4, so
`PAIR_ANALYSIS_NOT_READY`**. Validator probed with **214 deliberate violations and
214 caught**, 209 by rule and 5 by drift, the five being exactly the hand-edited
generated pages. 2019 bare-python tests run before commit.

New: `docs/data/mission-1.66.2-baseline-v1.json`,
`onyphe-public-documentation-reconciliation-v1.json`,
`onyphe-temporal-object-public-doc-review-v2.json`,
`onyphe-datascan-port-configuration-public-doc-review-v2.json`,
`onyphe-user-api-configuration-surface-review-v1.json`,
`onyphe-retention-public-doc-review-v2.json`,
`onyphe-contact-channel-reconciliation-v1.json`,
`onyphe-three-question-reassessment-v1.json`,
`onyphe-package-recomputed-v2.json`, `qualified-apparatus-readiness-v3.json` and
their rendered `.md`;
`infrastructure/scripts/render_documentation_reconciliation.py`; 84 tests in
`packages/inferred-claim-evaluator/python`.

Report: `docs/architecture/mission-1.66.2-report.md`.

## 1.100 — 2026-09-05 (Sprint 1 / Mission 1.66.1)

**`ONYPHE_MANUAL_DISPATCH_ATTESTED`.** The operator sent the approved enquiry
manually, seven minutes after Mission 1.66 merged reporting it as awaiting
execution, and attested to it afterwards. **This repository still sent nothing**,
and this is the first outward action in the project's history to have been
completed at all.

**MISSION 1.66 WAS NOT REWRITTEN, AND THAT IS THE STRUCTURAL DECISION.** Its
execution record still reads `APPROVED_AWAITING_MANUAL_EXECUTION`, its verdict
still reads outcome B, and its baseline is untouched. **Both were true when it
ran**, and editing them to read SENT would make a mission report describe a moment
it did not observe. History is a chain of four records — content approved,
dispatch approved, awaiting execution, operator-attested sent — and each says what
was established when it was written.

**THE STALE-RECORD HAZARD WAS CLOSED WITHOUT FALSIFYING ANYTHING.** A reader
meeting the Mission 1.66 record alone would take a historical state for the
current one. So that record gains **one appended forward pointer** naming this
attestation, and nothing else in it changes — the Mission 1.58 shape, where a
withdrawn selection was appended to rather than edited away. The pointer renders
on the page, so the historical document itself says which record continues it.
**The alternative was rejected explicitly**: mutating the status would have
required editing Mission 1.66's validator and four of its tests to describe a
different file, and a guard edited so that new work can pass is a guard that never
was.

**THE MOST CONSEQUENTIAL LINK IN THE CHAIN RESTS ON THE WEAKEST EVIDENCE
AVAILABLE, BECAUSE IT IS THE ONLY EVIDENCE THAT EXISTS.** The content answers to a
hash. The approval names that hash. The action the approval authorises is fixed by
seven bound fields. **The one fact that the message actually left rests on a person
saying so.** No sent-message artifact was imported and this repository never
observed the send, so the level is `OPERATOR_ATTESTED` and explicitly not
`BYTE_VERIFIED` — and the record states what the upgrade would take, because a
weaker level stated with its upgrade path is a position while one stated without
is a shrug. **A positive probe case proves the distinction is enforced rather than
merely refused**: an attestation with an imported artifact and a body hash equal
to the approved content is ACCEPTED.

**EVERY FIELD MATCHED, AND THE SENDER MATCHED NOTHING ON PURPOSE.** Recipient,
channel, subject and send count are the approved ones. The sender is
`thib.chm@gmail.com`, admitted under verdict `ALLOWED_BY_APPROVED_PLACEHOLDER`
rather than `MATCH`, because the envelope deliberately bound
`OPERATOR_CHOSEN_MAILBOX_AT_SEND_TIME` instead of a mailbox. **The cost Mission
1.65 stated in advance is the cost that was actually paid**: that envelope's hash
pins three fields of four, so the approved action never named which mailbox it
would come from. A cost written down before anyone could know whether it would
matter, and then incurred exactly as described, is the cheapest evidence available
that the reasoning was honest rather than decorative.

**THE FROZEN ENVELOPE LEARNED NOTHING FROM THE SEND.** Its sender placeholder is
not replaced, it is not marked sent, its dispatch count is still zero and no
approval was written into it. It records the permission; the attestation records
the event.

**A DEFECT IN THIS MISSION'S OWN GATE WAS FOUND BY CHECKING HOW A CASE WAS
CAUGHT.** The probe reported 157 of 157 caught — and one case, a record claiming
`CHECKED_NONE_FOUND` while recording that the mailbox was never searched, was
caught only by **render drift**. Re-render and it passed. **A case caught by drift
is a case a re-render releases**, and this one mattered: *checked and found
nothing* is materially stronger than *not checked*, and it is exactly the upgrade a
later mission would be tempted to make. Two repairs followed: a rule requiring that
a claim about what is in a mailbox be backed by having looked, and a probe that
now sends record mutations through `validate()` directly so drift can never stand
in for a rule. The final split is **152 caught by rule, 5 by drift**, and the five
are exactly the hand-edited generated pages where drift is the correct catcher.

**A SENT QUESTION IS STILL NOT AN ANSWER**, and the sentence three missions have
repeated is now being used for the case it was written for. ONYPHE stays B2
PARTIAL with port membership and post-30-day location fields UNKNOWN. The mailbox
was **not searched**, so the reply status is `NOT_CHECKED_AFTER_DISPATCH` and
explicitly not `NO_RESPONSE_EXISTS`. Netlas is untouched, with nothing guessed and
no obfuscation decoded. **Qualified apparatuses 0 of 4, so
`PAIR_ANALYSIS_NOT_READY`.**

0 emails sent by this repository, 0 connector executions, 0 mailbox searches, 0
follow-ups, 0 replies frozen, 0 replies interpreted, 0 measurement queries, 0
counts, 0 host records, 0 banners, 0 trials, 0 purchases. 0 canonical mutations, 0
sources registered, 0 governance reviews, 0 reliability values, 0 independence
groups, 0 model calls, 0 embeddings, no migration. Baseline verified unchanged:
325 / 325 / 33, 44 Claims, 45 revisions, 58 Evidence, 4 reliability assessments, 29
sources, head `0035`. Profile still UNCALIBRATED, Problem-Family still PARKED.
Validator probed with **157 deliberate violations and 157 caught**, plus one
positive case. 1935 bare-python tests run before commit.

New: `docs/data/onyphe-manual-dispatch-attestation-v1.json` and its rendered
`.md`; a forward pointer appended to
`onyphe-enquiry-dispatch-execution-v1.json`;
`infrastructure/scripts/render_dispatch_attestation.py`; 57 tests in
`packages/inferred-claim-evaluator/python`.

Report: `docs/architecture/mission-1.66.1-report.md`.

## 1.99 — 2026-09-05 (Sprint 1 / Mission 1.66)

**`ONYPHE_APPROVED_DISPATCH_AWAITING_MANUAL_EXECUTION`.** The operator's approval
arrived, was verified against a recomputed envelope hash, and is recorded as an
approval. **The action it authorises has not been performed**, and this mission's
whole job was to say so rather than to assume otherwise. **Nothing was sent.**

**AN APPROVAL IS NOT AN EXECUTION, AND THIS IS WHERE A DISPATCH LOG WOULD START
LYING.** A permission says an action MAY be performed; only a performance says it
WAS. The two are unusually easy to merge here because **once the approval exists,
every field an execution record needs is already known** -- recipient, subject,
body and channel are all frozen in the envelope the approval names. A record
could therefore fill itself in completely and be entirely fictional. So the
approval and the execution are two sections of one artifact, and `SENT` is
reachable only through an explicit operator confirmation plus an actual sender
mailbox that no frozen document contains.

**AND THE NEW HALF: THE REPOSITORY CANNOT VERIFY A MANUAL SEND AT ALL.** Missions
1.36.1 and 1.42.1 both stopped because a value was authorised and the keystroke
was not -- and there the keystroke happened INSIDE the repository, where a
terminal guard could require a person to be present. **A manual outbound send
happens in a mail client nothing here can observe.** No guard can establish it.
The repository can record an attestation and must say that is what it is, which
is why `BODY_POST_SEND_VERIFICATION` distinguishes `OPERATOR_ATTESTED` from
`BYTE_VERIFIED` and why the validator refuses the second without a body hash. **A
probe case proves the check discriminates rather than merely refusing**: a
correctly evidenced byte-verified send is ACCEPTED.

**THE APPROVAL WAS NOT WRITTEN INTO THE DOCUMENT IT APPROVES.** Mission 1.56
settled this shape for a frozen manifest: marking a document APPROVED changes the
bytes that were approved. Here the envelope hash covers only seven binding fields,
so an approval flag **would not have moved the hash** -- and it would still have
changed the artifact the operator read. So the envelope is byte-for-byte
untouched, its sender placeholder is not replaced, and the approval lives in the
execution record. **A guard now does a second job**: Mission 1.65's validator
asserts the envelope's `approval_recorded` is false, which it wrote to mean *this
mission stops before approval*, and which now keeps the approval OUT of the frozen
document. The field means THIS DOCUMENT RECORDS NO APPROVAL, never that no
approval exists, and that sentence is written into the record so a later reader
cannot derive the second from the first.

**THE ONE WAY THIS MISSION COULD HAVE QUIETLY GONE WRONG WAS AVAILABLE THE WHOLE
TIME.** A mail-capable connector sits in this runtime, the content is approved and
the recipient is established; one call would have made the action look finished,
with matching body, matching recipient and a hash that still verifies. **It would
have been a different action.** `outbound_channel` is one of the seven fields the
approved hash binds, so an automated send carrying identical text to the identical
recipient is not the approved action by another route -- and it would have been an
outward action on the operator's behalf, from a mailbox they never named.
`CONNECTOR_EXECUTIONS = 0`.

**THE INTEGRITY CHECKS WERE FROZEN BEFORE ANY SEND, WHICH IS THE ONLY TIME THEY
MEAN ANYTHING.** Recipient, channel, subject and body hash must match the approved
action; one approval authorises exactly one send; a duplicate is reported rather
than tidied away, because **a sent message cannot be unsent**; and a divergence is
a fact about the execution rather than a defect in the approval, so the historical
envelope is never repaired to match what was actually done.

**TWO ABSENCES ARE RECORDED AS THE WEAKER TRUE CLAIM RATHER THAN THE STRONGER
CONVENIENT ONE.** The approval's exact time is `NOT_ESTABLISHED` with a true lower
bound -- the moment PR #108 merged, before which the hash it names did not exist
on main -- because a timestamp nobody can check is worth less than a bound that
holds. And the record says only that **the repository holds no provider reply and
the operator's mailbox was not read**, never that no reply exists: the brief asks
for an operator statement as dispatch evidence and never asks for a mailbox to be
searched, so searching it would have been an access nobody requested and would
have replaced an attestation with an inference.

**NOTHING ELSE MOVED.** ONYPHE stays B2 PARTIAL with port membership and
post-30-day location fields UNKNOWN; Netlas stays A7 PASS / A8 PARTIAL with its
content approval valid, its recipient unestablished and nothing guessed or
decoded. **Qualified apparatuses 0 of 4, so `PAIR_ANALYSIS_NOT_READY`.** 0
first-party retrievals, 0 measurement queries, 0 counts, 0 host records, 0
banners, 0 trials, 0 purchases, 0 enquiries sent, 0 connector executions, 0
follow-ups, 0 mailbox searches, 0 replies frozen, 0 replies interpreted. 0
canonical mutations, 0 sources registered, 0 governance reviews, 0 reliability
values, 0 independence groups, 0 model calls, 0 embeddings, no migration. The
Mission 1.56 Claim is untouched, the profile is still UNCALIBRATED and
Problem-Family is still PARKED. Validator probed with **193 deliberate violations
and 193 caught**, plus one positive case asserting a legitimate send is accepted.
1878 bare-python tests run before commit.

New: `docs/data/mission-1.66-baseline-v1.json`,
`onyphe-enquiry-dispatch-execution-v1.json`,
`approved-dispatch-execution-v1.json` and their rendered `.md`;
`infrastructure/scripts/render_dispatch_execution.py`; 58 tests in
`packages/inferred-claim-evaluator/python`.

Report: `docs/architecture/mission-1.66-report.md`.

## 1.98 — 2026-09-05 (Sprint 1 / Mission 1.65)

**`NETLAS_RECIPIENT_PENDING_ONYPHE_ENQUIRY_FROZEN`.** One enquiry is now
dispatch-ready and awaiting a single operator approval; the other is exactly where
Mission 1.64 left it, waiting on a string. **Nothing was sent.**

**THE RULE THIS MISSION FREEZES IS `CONTENT_APPROVAL_IS_NOT_DISPATCH_APPROVAL`,
AND IT IS THREE GATES RATHER THAN ONE.** Content approval says a body may be sent;
recipient establishment says who may read it; channel authorisation says by what
mechanism. The Netlas enquiry has held the first since Mission 1.61 and has never
held the other two, which is why an approval issued four missions ago is still
valid and still unusable. The contract is **not** an apparatus-requirements
registry entry: the registry governs measurement apparatuses and this governs an
operator action, so the registry stays at 14.

**AN ENVELOPE HASH HAD TO SURVIVE BEING WRITTEN INTO THE ENVELOPE.** Mission 1.56
settled the frozen-document shape by keeping a hash outside the bytes it names,
and an envelope cannot do that, because the thing the operator approves IS the
envelope. So the digest is taken over a named set of **binding fields** — enquiry
id, content hash, recipient, channel, sender, subject, content version — and
excludes the hash, the approval string and everything about when the record was
written. Recording the hash therefore does not move it, which is checked by
recomputing it from the file as stored rather than asserted. **The digest binds the
ACTION and not the document**: changing the recipient, the channel, the sender or
the subject moves it, and changing the recorded date does not.

**THE RECIPIENT WAS JUDGED ON PROVENANCE RATHER THAN ON THE SPELLING OF THE
ADDRESS.** The established ONYPHE mailbox has a conventional local part, and
Mission 1.64's validator lists exactly that string among the mailbox forms it
refuses. That rule forbids **inferring** a mailbox from convention; this one was
read off two first-party pages that print it as a live link. A string ban would
have refused a correctly established address while still admitting a guessed one
that happened to look unusual, so the check is on how the address was obtained.
Three other published addresses were seen and excluded by name, including a demo
address — **writing to it would be requesting a trial, and a zero-cost trial
destroys preregistration exactly as a paid one would.**

**AN ENVELOPE THAT NAMES NOBODY CARRIES NO HASH.** The Netlas envelope is a
TEMPLATE: no recipient, no channel evaluated, no digest, no approval string, not
approvable, and no packet generated. A hash is an approval handle, and producing
one for an incomplete action would let an operator approve a send whose reader is
blank. The page carrying the address was **not re-fetched**, because three
missions have established that automated retrieval returns a placeholder there.

**A CONNECTOR PRESENT IN THE RUNTIME IS STILL NOT CHANNEL AUTHORISATION.** The
mail-capable connector is recorded `AVAILABLE_NOT_AUTHORIZED` and the channel is
the operator sending it themselves. The sender is a **placeholder**, permitted for
manual send only because under manual send the sender genuinely is not determined
until the moment of sending — and **its cost is stated rather than hidden**: the
hash binds three of the four fields, and pinning the fourth would produce a
different envelope that SUPERSEDES this one rather than editing it.

**THE ONYPHE ENQUIRY IS EXACTLY THE THREE RESIDUALS MISSION 1.64 FROZE.** Record
lifecycle, datascan port set, and which fields survive beyond thirty days. No
fourth question was added, nothing already documented is re-asked — question 3
states the known 4 KB truncation as known and explicitly declines to raise it
again — and the body asks for no records, no account, no trial and nothing
commercial. **It asks what the system does and never whether the system
qualifies**, because asking a provider to confirm its API is observation-addressable
is asking it to grade our gate.

**THE VALIDATOR CAUGHT THIS MISSION'S OWN RECORD**, for the seventh time in the
`testing-strategy.md` §23 shape: the enquiry's preamble denied asking for anything
commercial and the denial contained the forbidden word, inside the sendable body
where the scan is strictest. Reworded rather than scoped, because scoping the scan
around a denial is how a structural check stops checking.

**AND THE PROBE CAUGHT ITS OWN DEFECT BEFORE THE GATE DID.** One case substituted a
heading absent from the approved document, so it mutated nothing and reported an
escape from a working gate — the exact Mission 1.64 shape, caught here by a
mutation assertion the probe now makes on every case. **A probe case that changes
nothing tests nothing.**

**THE ASYMMETRY IS A FACT ABOUT TWO CONTACT PAGES AND NOT A RANKING.** One provider
prints its address as a live link and the other serves it through an obfuscation
mechanism. Neither fact bears on whether the apparatus is a good measurement
instrument, and **dispatch readiness is progress on the ASKING rather than on the
apparatus**: both remain unresolved or worse, qualified apparatuses stay **0 of 4**,
and `PAIR_ANALYSIS_NOT_READY`.

2 first-party retrievals, **0 measurement queries, 0 counts, 0 host records, 0
banners, 0 downloads, 0 trials, 0 purchases, 0 enquiries sent, 0 connector
executions, 0 credentials written**. 0 canonical mutations, 0 sources registered,
0 governance reviews, 0 Claims, 0 Evidence, 0 reliability values, 0 independence
groups, 0 Scores, 0 model calls, 0 embeddings. The Mission 1.56 Claim is untouched,
the profile is still UNCALIBRATED and Problem-Family is still PARKED. The Netlas
enquiry v1 was **not edited** and still answers to its approved hash. Validator
probed with **204 deliberate violations and 204 caught**, four of which edited the
approved document. 1820 bare-python tests run before commit.

New: `docs/data/mission-1.65-baseline-v1.json`,
`onyphe-technical-methodology-enquiry-v1.json`,
`outbound-dispatch-envelope-contract-v1.json`,
`netlas-dispatch-envelope-v1.json`, `onyphe-dispatch-envelope-v1.json`,
`dual-enquiry-readiness-v1.json` and their rendered `.md`;
`onyphe-enquiry-dispatch-packet-v1.md`, generated from the frozen enquiry rather
than retyped; `infrastructure/scripts/render_dispatch_envelope.py`; 51 tests in
`packages/inferred-claim-evaluator/python`.

Report: `docs/architecture/mission-1.65-report.md`.

## 1.97 — 2026-09-05 (Sprint 1 / Mission 1.64)

**`ANCHOR_CONTACT_CHANNEL_STILL_NOT_ESTABLISHED`.** The mission had an approved
message, a hash that verifies under every plausible boundary, and a mail-capable
connector in the environment. **It sent nothing**, because the one input it needs
is a string only a person reading a page can supply.

**THE APPROVAL NAMES A DOCUMENT AND NOT A RECIPIENT, WHICH IS WHY IT HAS
SURVIVED THREE MISSIONS OF WAITING.** The frozen enquiry records its recipient as
TO_BE_SUPPLIED_BY_OPERATOR, so the address travels in a dispatch packet beside the
document rather than inside it. Writing a real address into the body would change
its bytes and void the approval, and the design that avoids that was made in
Mission 1.61 before anyone knew the address would be hard to get.

**THE HASHING BOUNDARY IS DOCUMENTED RATHER THAN ASSUMED.** The digest was
recomputed over the raw bytes as stored, over a UTF-8 decode and re-encode, and
over a CRLF-to-LF normalisation. All three agree, because the file is LF-only.
That is worth recording rather than assuming: on a Windows working tree a line
ending rewrite would have split them, and a mission that tested one boundary would
not know which one the approval named. The document also survives regeneration by
its own renderer byte for byte, which two CI gates now enforce together.

**THREE REASONS NOT TO SEND, AND THE MISSION RECORDS ALL THREE.** There is no
verified recipient. Sending mail from the operator's own account is an outward
action on their behalf, and an approval of TEXT is not an approval of a CHANNEL.
And the brief permits only an already-authorised outbound mechanism, which a
connector merely being present in the environment is not. Any one of the three
would have been sufficient; the record states them in order so a later mission
knows which one to clear first.

**NO MAILBOX WAS GUESSED AND THE OBFUSCATION WAS NOT DECODED.** The address is
published for people to read, and a person reading it is the route the publisher
intended. Defeating an anti-scraping mechanism to obtain it would be
circumvention, and a guessed mailbox would put an unapproved recipient beside an
approved message.

**THE THREE CANDIDATE READS COMPLETED AND NO SLOT MOVED.** The record-lifecycle
question gained four converging documented statements — time-range functions
described as querying *data collected some hours ago*, a default sort where *latest
result is displayed first on output*, up to a hundred results per category per
asset inside thirty days, and an explicit split between a recent-only surface and
a historical one — **and none of them states the model**. Every one is fully
explained by one document per service per port with no repetition over time. B2
stays PARTIAL, and the residual narrowed to a single named case: a service
observed during a window AND again afterwards, which an append store returns for
that window and a maintained store does not.

**THE PORT QUESTION IS NOW AN ESTABLISHED GAP RATHER THAN A SUSPECTED ONE.** The
published scanned-port list was asked directly for every category section it
carries and it carries exactly one, for a category that is not the relevant one.
The datascan set is documented by size and cadence and never by membership.

**THE RETENTION QUESTION WAS ASKED IN THE SECOND PLACE IT COULD LIVE.** The field
documentation carries no per-field retention annotation at all, so whether the
address, the observation timestamp and the scanner node fields survive stays
UNKNOWN — and was not guessed in either direction. Reasoning that a scan archive
without addresses would be useless, so they must survive, is an argument from what
a sensible provider would do rather than from what this one documents.

**THE PROBE FOUND A REAL GAP IN THIS MISSION'S OWN VALIDATOR.** Marking the frozen
enquiry as sent escaped: the validator checked the dispatch record's send state
and never the frozen document's own delivery fields, which Mission 1.63's
validator had checked and this one dropped. A hash guards the body and says
nothing about the fields beside it. Repaired, and two further frozen-document cases
added. **A second probe case was itself defective**: it substituted a literal that
does not appear in the approved body, so it mutated nothing and reported an escape
from a gate that was working. A probe case that changes nothing tests nothing.

**BOTH REMAINING APPARATUSES ARE NOW BLOCKED ON THE SAME KIND OF THING.** The
anchor has six unpublished operational questions and the candidate has three, and
every one of the nine is a methodology question asking for no data. That is one
instrument asked twice rather than two different problems. The candidate's three
are recorded as questions rather than as gaps, because that is the shape they are
now in.

Registry unchanged at 14. The rule this mission demonstrates — that an approval
names a document and a recipient must live outside the hashed range — is a
property of approval artifacts rather than of measurement apparatuses, and the
requirement registry is the apparatus registry.

7 first-party retrievals across three targets. **0 measurement queries, 0 counts,
0 host records, 0 banners, 0 facets, 0 downloads, 0 trials, 0 purchases, 0
enquiries sent, 0 credentials written.** 0 canonical mutations, 0 sources
registered, 0 governance reviews, 0 Claims, 0 Evidence, 0 reliability values, 0
independence groups, 0 Scores, 0 model calls, 0 embeddings. The Mission 1.56 Claim
is untouched, the profile is still UNCALIBRATED and Problem-Family is still
PARKED. **Qualified apparatuses 0 of 4, so `PAIR_ANALYSIS_NOT_READY`**, and no
pair gate was evaluated. Validator probed with **98 deliberate violations and 98
caught**, three of which edited the approved document. 1769 bare-python tests run
before commit.

New: `docs/data/mission-1.64-baseline-v1.json`,
`anchor-enquiry-dispatch-review-v1.json`,
`onyphe-datascan-record-lifecycle-v1.json`,
`onyphe-datascan-port-configuration-v1.json`,
`onyphe-post-30d-field-retention-v1.json`,
`onyphe-package-final-recompute-v1.json`,
`apparatus-readiness-after-enquiry-dispatch-v1.json` and their rendered `.md`;
`anchor-enquiry-manual-dispatch-packet-v1.md`, generated from the frozen enquiry
rather than retyped; `infrastructure/scripts/render_enquiry_dispatch.py`; 52 tests
in `packages/inferred-claim-evaluator/python`.

Report: `docs/architecture/mission-1.64-report.md`.

## 1.96 — 2026-09-05 (Sprint 1 / Mission 1.63)

**`ANCHOR_ENQUIRY_STILL_REQUIRED_ONYPHE_UNRESOLVED`.** Four named reads, seven
retrievals of a budget of eight, and **zero gate verdicts changed**. Three of the
four reads moved evidence anyway, one closed a named risk outright, and one
refused a verdict it had nearly recorded.

**THE FINDING WORTH CARRYING IS THAT A RETRIEVAL SUMMARY IS NOT A DOCUMENT.** The
first read of the candidate's query-language page reported, in analytical prose,
that its time-range functions filter on time of data collection and not on record
modification dates, and filter by observation period rather than record state.
That is exactly the distinction the temporal-object test turns on, phrased as a
contrast between the two candidate readings, and it would have moved B2 from
PARTIAL to PASS. It arrived without quotation marks, unlike the timestamp
definition on the data-model page, so it was re-read verbatim. **The page does not
contain that sentence.** What it contains is a section described as allowing
search through historical data and four calendar-bucket boundary definitions.
Mission 1.61 re-read the anchor's lineage sentence for the same reason and the
re-read CONFIRMED it; the procedure is identical and the answer went the other
way. A PASS resting on a sentence that does not exist was not recorded.

**THE PORT-22 READ FOUND A PORT LIST FOR THE WRONG CATEGORY.** The candidate's
published scanned-port list is headed for the **ctiscan** category and documents
5,054 TCP ports including 22. The construct's protocol-native evidence lives in
**datascan**, whose refresh documentation describes a 500-port cycle whose
membership is published nowhere, and whose retention is seven months against
ctiscan's one. A configuration fact published for one resource does not establish
it for another, which is RESOURCE_SPECIFIC_LINEAGE applied to configuration.
Verdict `PORT_22_STATUS_UNKNOWN`, and the gap is new: before this read the
question was unread, and it is now a named category mismatch answerable by one
document.

**THE RETENTION READ RESOLVED, AND IN THE CANDIDATE'S FAVOUR ON THE LOAD-BEARING
HALF.** Verbatim: *For data older than 30 days, we remove some fields as they are
less useful, and we truncate data field to 4KB*. The sentence distinguishes two
operations and **names the raw response field as the one TRUNCATED**, placing it
outside the set removed. A four-kilobyte truncation does not touch the beginning
of an identification string of tens of bytes, so the predicate survives and B3 is
not reopened. Mission 1.62 flagged this as the risk that could end protocol-native
exposure at thirty days; it does not. Which other fields are removed is still not
named, and whether the observation timestamp and the address survive is
`UNKNOWN` rather than guessed in either direction.

**THE ANCHOR READ EXHAUSTED ITS LAST NAMED LEAD WITHOUT CLOSING ANYTHING.** The
indices operation is located, its documented path recorded, and the rendered API
reference truncates before the response schema at the operation's own anchor. The
endpoint was **not executed**: section 5 permits calling a configuration endpoint
only where evidence proves its response carries no measurement, and the evidence
that would prove it is the schema that could not be read. Calling it to find out
whether calling it is safe is circular. `PORT_22_WINDOW_COVERAGE_NOT_ESTABLISHED`,
with no inference drawn from the current list, from list cardinality, from the
absence of recorded removals, or from the endpoint merely existing.

**A8 WAS RECOMPUTED AND NOT ONE TOPIC MOVED.** Ten topics, two answered, four
partial, four unknown, `changed_this_mission` **0**. That is the honest count, and
recording it beats converting *we now know which page to read* into progress. Five
load-bearing topics remain unresolved and six of the seven frozen enquiry
questions target them.

**THE ENQUIRY IS UNCHANGED AND NO DUPLICATE HASH WAS MANUFACTURED.** All seven
questions reassessed after the four reads, all seven `STILL_UNRESOLVED`, so CASE A
applies: v1 remains current, frozen and unsent on Mission 1.61's exact hash. Three
of the four reads were candidate questions and the enquiry is addressed to the
anchor, which is why four reads produced zero answered questions and is stated
rather than left looking like waste.

**ONE OFFERED REGISTRY RULE WAS ADDED AND ONE WAS DECLINED.**
`APPARATUS_CONFIGURATION_MUST_BE_TIME_ADDRESSABLE` is added, demonstrated by both
apparatuses independently: each publishes a current port list and neither binds it
to a window. It is distinct because OBSERVATION_ADDRESSABLE_EXPOSURE governs when
the observation happened and this governs when the configuration applied, and an
apparatus can expose a perfect observation timestamp while leaving you unable to
say whether it was probing the port then. `FULL_FIDELITY_RETENTION_IS_PART_OF_
ACQUISITION_CONTRACT` was **declined**: retention resolved favourably, so the
evidence demonstrated the opposite of the failure the rule anticipates, and
`MAX_FULL_FIDELITY_RETRIEVAL_DELAY` was frozen as a per-apparatus duration
instead. Registry 13 to 14.

**TWO DEFECTS IN THIS MISSION'S OWN TOOLING WERE FOUND AND FIXED.** A validator
guard compared a field to the literal `NONE` where the record states `NONE` and
then explains it, so the guard could never fire; repaired to a prefix test and
proved firing. And a mechanical collapse of nested `if` statements folded a
sibling check inside a `raise`, making it unreachable while still looking like a
check — caught because the probe went from 123 caught to 122 caught and one
escaped, then repaired by hand and re-audited over the AST for any other
unreachable statement. **A guard that cannot fire is the recurring shape in this
repository, and the probe is what makes it visible.**

**A MISSION 1.62 TEST WAS RE-POINTED RATHER THAN DELETED.** It pinned the registry
length at 13, which this mission's legitimate addition made false. A test pinning a
total is a test asserting the registry never grows; it now asserts that no earlier
requirement is dropped and that no name is duplicated.

7 of 8 first-party retrievals. **0 measurement queries, 0 counts, 0 host records,
0 banners, 0 facets, 0 downloads, 0 configuration endpoints executed, 0 trials, 0
purchases, 0 enquiries sent.** 0 canonical mutations, 0 sources registered, 0
governance reviews, 0 Claims, 0 Evidence, 0 reliability values, 0 independence
groups, 0 Scores, 0 model calls, 0 embeddings. The Mission 1.56 Claim is
untouched, the profile is still UNCALIBRATED and Problem-Family is still PARKED.
**Qualified apparatuses 0 of 4, so `PAIR_ANALYSIS_NOT_READY`** and no pair gate was
evaluated. Validator probed with **123 deliberate violations and 123 caught**,
three of which edited the frozen enquiry. 1717 bare-python tests run before commit.

New: `docs/data/targeted-documentation-closure-baseline-v1.json`,
`netlas-indices-port-window-review-v1.json`,
`onyphe-datascan-temporal-object-review-v1.json`,
`onyphe-scanned-port-review-v1.json`,
`onyphe-full-fidelity-retention-review-v1.json`, `anchor-a8-recomputed-v1.json`,
`onyphe-package-recomputed-v1.json`, `qualified-apparatus-readiness-v1.json`,
`mission-1.61-enquiry-reassessment-v1.json` and their rendered `.md`;
`infrastructure/scripts/render_documentation_closure.py`; 61 tests in
`packages/inferred-claim-evaluator/python`.

Report: `docs/architecture/mission-1.63-report.md`.

## 1.95 — 2026-09-05 (Sprint 1 / Mission 1.62)

**`ANCHOR_ENQUIRY_REQUIRED_PARTNER_PACKAGES_COMPLETE`.** All three partner
packages are COMPLETE under one contract and none of the three individually
qualifies. The anchor's A8 stays PARTIAL. No pair was compared, ranked or
selected.

**THREE COMPLETE PACKAGES, THREE DIFFERENT FAILURES, AND THAT IS THE RESULT.**
Mission 1.60 left all three candidates at a documentation wall, which told us
nothing about any of them. Now each is decided on its own merits and each fails
somewhere different. **LeakIX fails B2 on documented timestamp semantics**: its
three date fields are an indexing date, a first-detection date and a
last-detection date, and none is an observation event. That is Mission 1.59's
failure exactly — a window filter over a last-seen field selects hosts whose last
detection fell inside the window, so a host present throughout it is missing from
the set. **Its B3 passes**, on a documented SSH banner field, and the pass is
recorded even though the package fails, because a gate is judged on its own
question. A perfect banner with no pre-retrieval observation-window selector still
fails, and one may not compensate for the other.

**SHADOWSERVER FAILS ON A DISTINCTION THIS ARC HAD NOT YET NAMED.** It performs
its own daily internet-wide scanning, and its reporting API states that a
requester only gets the data on the networks they are responsible for and will
not be able to get data on other networks or systems, with access limited to
members of the reports group. **It scans everything and can show us only ours.**
Its observation-window selector is the cleanest of the three candidates and its
frame is the requester's own networks, so two requesters retrieve two different
populations and no proposition about the internet can be witnessed through it.
That is a FAIL rather than an UNKNOWN, because it is an affirmative documented
statement rather than a silence.

**ONYPHE IS UNRESOLVED WITH FOUR PARTIAL SLOTS, AND ITS B3 NOW PASSES.** Mission
1.61 recorded that the raw field's NAME was unestablished; the data model
documents a `data` field holding the raw application response, full-text
searchable up to one megabyte, kept distinct from a normalised `summary`. **Its
B2 turns on an ambiguity that was not resolved favourably**: the timestamp field
is documented as the moment the data was collected, and in the same sentence as
allowing tracking of when a service was LAST OBSERVED. Those are two different
temporal objects, and resolving the ambiguity in the direction that keeps a
candidate alive is what this arc has refused four times. It also documents a
scanner node identifier and country per record, and weekly scans alternating
origin country week to week — so its vantage is `MULTI_VANTAGE_SEPARABLE`, which
is more than the anchor publishes about itself.

**THE ANCHOR'S A8 STAYS PARTIAL AND ONE ANSWER WAS DOWNGRADED, WHICH IS THE AUDIT
WORKING.** Ten topics: two answered, four partial, four unknown. **FRAME moved
from ANSWERED to PARTIAL** once eligible frame and attempted frame were separated:
the address range is declared and which addresses were actually probed in a cycle
is not. **RETRY moved from PARTIAL to UNKNOWN** once the API's throttling and
retry parameters were correctly identified as governing the CLIENT retrying the
API rather than the SCANNER retrying a probe — answering a measurement question
with a transport-library setting would have been the easiest mistake available.
Sampling, vantage and missingness remain unknown, and the most likely remaining
first-party document, the data collection policy, closes none of them.

**TWO RETRIEVAL-SURFACE CONSTRAINTS WERE ESTABLISHED THAT NOBODY KNEW.** The API
reference states that if the index parameter is not supplied, the search is
conducted using the latest publicly available internet scan data — the verbatim
confirmation of Mission 1.61's A2 bound, and the reason the second new registry
rule exists. And **the count endpoint returns an ESTIMATE with an error margin
not exceeding three per cent above one thousand results**. The construct is a
count of distinct addresses across the public IPv4 space and will exceed one
thousand, so a threshold evaluated against that endpoint would compare a bound
against an estimate whose error band could decide the direction. **A SUPPORTS or
CONTRADICTS produced by the estimator rather than by the world** is precisely the
artefact-recorded-as-a-finding failure this layer must not have. It bounds HOW
the value must be obtained rather than whether it can be, and the documented
download endpoint is the alternative.

**THE FROZEN ENQUIRY WAS NOT EDITED AND NO DUPLICATE HASH WAS MANUFACTURED.** All
seven of its questions were compared against the updated matrix and all seven are
STILL_UNRESOLVED, so v1 remains current, no v2 was cut, and Mission 1.61's exact
hash stays authoritative. The count-estimate finding was deliberately NOT added to
it: it is documented rather than missing, so it is an answered constraint and not
a question, and adding it would ask the provider to restate its own documentation.

**A CONTACT PAGE WAS FOUND AND NO ADDRESS WAS INVENTED.** A first-party legal page
carries a printed contact instruction; the address is served through an
obfuscation mechanism and the retrieval returned a placeholder. That is recorded
as `FIRST_PARTY_CONTACT_CHANNEL_NOT_ESTABLISHED` beside the page that carries it,
because a valid question and a valid channel are two different facts and guessing
an address would fabricate a fact about a provider.

**THE BRIEF'S OWN INSTRUCTION CAUGHT AN ATTRIBUTION ERROR IN THE BRIEF.** It
assigned the vetted-private-API blocker to one candidate and the thirty-day
field-removal blocker to another, and told the mission to resolve each from the
artifact. The artifact assigns them the other way round, and both were pursued
against the candidate that actually carries them.

**TWO REQUIREMENTS JOIN THE REGISTRY, NOW THIRTEEN**:
`THE_RETRIEVABLE_FRAME_IS_NOT_THE_MEASURED_FRAME`, and
`DEFAULT_DATA_SURFACE_MUST_NOT_OVERRIDE_QUALIFIED_EXPOSURE_PATH`, which governs
implementation where OBSERVATION_ADDRESSABLE_EXPOSURE governs selection. Earlier
missions' records were **not rewritten**.

24 of 24 first-party retrievals, five of which returned nothing usable and are
counted anyway. **0 measurement queries, 0 counts, 0 host records, 0 banners, 0
facets, 0 downloads, 0 trials, 0 purchases, 0 enquiries sent.** 0 canonical
mutations, 0 sources registered, 0 governance reviews, 0 Claims, 0 Evidence, 0
reliability values, 0 independence groups, 0 Scores, 0 model calls, 0 embeddings.
The Mission 1.56 Claim is untouched, the profile is still UNCALIBRATED and
Problem-Family is still PARKED. Validator probed with **126 deliberate violations
and 126 caught**, three of which edited the frozen enquiry. 1656 bare-python tests
run before commit.

New: `docs/data/anchor-operational-closure-baseline-v1.json`,
`anchor-operational-methodology-v1.json`, `anchor-sampling-frame-review-v1.json`,
`anchor-vantage-review-v1.json`, `anchor-port-window-review-v1.json`,
`partner-shadowserver-package-v1.json`, `partner-onyphe-package-v1.json`,
`partner-leakix-package-v1.json`, `partner-package-completion-v1.json`,
`anchor-operational-closure-and-partner-packages-v1.json` and their rendered `.md`;
`infrastructure/scripts/render_operational_closure.py`; 64 tests in
`packages/inferred-claim-evaluator/python`.

Report: `docs/architecture/mission-1.62-report.md`.

## 1.94 — 2026-09-05 (Sprint 1 / Mission 1.61)

**`ANCHOR_LINEAGE_CONFIRMED_OPERATIONAL_QUESTIONS_REMAIN`**, with
`PARTNER_DOCUMENTATION_RECOVERED` beside it. The sentence four missions said the
documentation did not contain is in the documentation, and reading it took two
retrievals of one page.

**A7 closes at LEVEL 2 and the standard was not lowered to close it.** The
apparatus states, first-party and verbatim, that all the data is collected
independently by itself, that it does not rely on third parties or aggregators,
and that every record is obtained and indexed directly by the platform — followed
by a clause naming *the only exceptions* as threat intelligence shown in one tool
and geolocation supplied by partners. That is an affirmative claim with a CLOSED
exception list, and each exception was then checked against the load-bearing
predicate one by one: a reputation annotation is not the presence of a service on
a host, and where an address sits is not whether it answered on a port. Neither
is load-bearing, so the gate passes. **A LEVEL 1 statement would not have closed
it**, and this mission supplies the contrast from the other side: one partner
candidate says its data comes from daily internet-wide scans, sinkholes, honeypot
sensors, sandboxes, blocklists **and many other sources** — an affirmative claim
whose list does not end, which cannot be checked against anything.

**The blocker narrowed rather than moved.** Mission 1.60 reported two blocking
gates and said both close by reading or asking. One closed by reading. The anchor
now reads seven PASS, one PASS_WITH_STATED_BOUNDS and one PARTIAL, and
`which_gates_block` goes from `["A7", "A8"]` to `["A8"]`. **It still does not
individually qualify**, because the gate set is conjunctive and one PARTIAL is
one short.

**A8 moved without passing, and the movement is that the questions are now
enumerated.** Eleven operational questions asked against the published
documentation: four answered, four partial, three unanswered. Answered are the
address frame, **port 22's inclusion in the current scanned list** — which
Mission 1.60 explicitly recorded as not established — the record identity, which
settles that one record is one service response so a count of addresses must be a
DISTINCT count and never a row count, and the scan-date semantics. Unanswered are
**sampling**, failure semantics and vantage, and sampling is the load-bearing one:
`SAMPLING_IS_LOAD_BEARING` says two apparatuses cannot be compared as one count
unless both expose the same population definition.

**A BOUND WAS FOUND ON A GATE A PREVIOUS MISSION PASSED, AND RECORDING IT IS THE
AUDIT WORKING.** The apparatus's DEFAULT search surface is a maintained
current-state view: its own documentation says that when a subnet is fully
scanned it *replaces* the previous version in the default output, and recommends
searching without specifying an index to get the most recently collected complete
data. **That is `MAINTAINED_CURRENT_STATE_LAST_CHANGE`, the exact temporal object
Mission 1.59 rejected.** A2 still passes, because the gate asks whether a window
is selectable in the request and the dated index mechanism is documented and
selectable — but the pass rests entirely on the NON-DEFAULT path, and a collector
using the default would be reading the rejected temporal object while a record
elsewhere said the gate had passed. The bound is written into the gate table.

**Vantage moved from `NOT_ESTABLISHED` to `NOT_DOCUMENTED`**, which is the
Mission 1.35 distinction: empty because nobody looked and empty because somebody
looked are different facts. Three pages and the response schema were consulted;
no scanner count, no locations, and **no record field identifies a scanner node
or probe origin**, so vantage could not be established after the fact even by
inspecting retrieved data. It is recorded before pairing because it is where
`FRAME_INSIDE_THE_DEFINITION` would recur: if each apparatus measures the hosts
reachable from its own network, the frame has moved inside the metric.

**Port-22 window coverage gives TWO answers and the record refuses to collapse
them.** Current inclusion is ESTABLISHED. Window addressability is
`PORT_22_NOT_ESTABLISHED`: the changelog dates the SIZE of the port list — one
entry doubling it, a later one taking it past a thousand — and never its
MEMBERSHIP, so the list as of any past date is not reconstructable. No removal is
recorded anywhere, which is favourable evidence about direction and **is not a
guarantee**, because an absence of recorded removals is an absence and this arc
has refused to read a positive claim out of a negative space four missions
running.

**All three partner candidates had their documentation recovered, and the wall
was the path rather than the apparatus.** Each failure has a named cause: one had
moved its documentation twice, ending on a GitHub wiki its own site now redirects
to; one keeps its documentation on a search subdomain rather than the marketing
domain both Mission 1.60 paths tried; one had a path one level too deep. Four of
eighteen B-slots are established, five partial, nine unread. **No partner is
qualified, ranked or selected**, and the record names the preference it declined
to express: one candidate emerged with a documented multi-continent vantage, a
documented weekly frame and a published retention table, which is more than the
anchor publishes about itself on two of those three — and treating that as a lead
would be picking a partner from a first pass in which two rivals had pages that
did not load. Two precise blockers are recorded for the next mission instead: one
candidate's API is described as mostly private to vetted subscribers, which would
make every other gate moot, and another documents that after 30 days it removes
*some fields* and truncates retained raw responses, which would end protocol-native
exposure at 30 days if the banner is among them.

**An enquiry is drafted and NOT sent.** Seven questions, one per unresolved
operational point, and **nothing already documented is asked** — the validator
refuses a question whose topic the operational record marks ANSWERED. It requests
no data, no access, no trial and no price. Its rendered form hashes to
`310acf288244453cd0a928197386cbf8311ded278e4dcdd22b70412807a049c4`, recorded in
the closure record rather than in the enquiry, because writing a hash into the
document it is a hash of changes the bytes it was frozen at. **No recipient
address is recorded**: none was retrieved first-party during the mission, and
inventing one would be fabricating a fact about the apparatus.

**The validator caught this mission's own record, and the fix was structural.**
The forbidden-ask scan refused the enquiry's own sentence saying it asks for no
trial and no evaluation account — `testing-strategy.md` §23 for the sixth time.
The repair scopes the scan to the text that would actually be TRANSMITTED rather
than weakening the rule, which is also stricter: the sendable body is the only
place those phrases could do harm.

**Two requirements were added to the registry, which now carries eleven**:
`ENUMERATED_EXCEPTIONS_MAKE_A_LINEAGE_CLAIM_CHECKABLE` and
`LINEAGE_EXHAUSTIVENESS_IS_NOT_FRAME_EXHAUSTIVENESS`. The second is the one most
easily lost: that every record was self-collected says nothing about which
addresses were reached, so a lineage sentence must never be cited for coverage.
Mission 1.60's own records were **not rewritten** — they still read
`ANCHOR_B_LINEAGE_PARTIAL` blocking A7 and A8, which is what that mission found.

16 of 20 first-party documentation retrievals — anchor 7 of 8, partners 9 of 12.
**0 queries executed, 0 counts, 0 host records, 0 facets, 0 trials, 0 purchases.**
0 canonical mutations, 0 sources registered, 0 governance reviews, 0 collectors,
0 threshold registrations, 0 Claims, 0 Evidence, 0 reliability values, 0
independence groups, 0 Scores, 0 Opportunity changes, 0 model calls, 0 embeddings.
The Mission 1.56 Claim is untouched, the profile is still UNCALIBRATED and
Problem-Family is still PARKED. Validator probed with **101 deliberate violations
and 101 caught**. 1592 bare-python tests run before commit.

New: `docs/data/anchor-documentation-confirmation-baseline-v1.json`,
`anchor-lineage-review-v1.json`, `anchor-operational-reviewability-v1.json`,
`anchor-vantage-model-v1.json`, `anchor-port-window-coverage-v1.json`,
`partner-documentation-recovery-v1.json`,
`anchor-lineage-and-documentation-closure-v1.json`,
`anchor-technical-lineage-enquiry-v1.json` and their rendered `.md`;
`infrastructure/scripts/render_anchor_lineage_closure.py`; 63 tests in
`packages/inferred-claim-evaluator/python`.

Report: `docs/architecture/mission-1.61-report.md`.

## 1.93 — 2026-09-05 (Sprint 1 / Mission 1.60)

**`APPARATUS_LINEAGE_NOT_AFFIRMATIVELY_ESTABLISHED`.** No pair selected. The
anchor apparatus requalified on both gates that killed the previous two pairs,
and what blocks it now is a sentence its documentation does not contain.

**Applying the gates before choosing worked.** That was the whole point of the
new ordering, and it changed what the mission found. The anchor passes A2 on two
independent mechanisms: a request parameter selecting a data-collection date, and
date ranges over a per-record `scan_date` documented as recording when the
scanning that generated the response occurred, with daily scan volumes
downloadable as dated files on top. The window is chosen in the request, not
discovered after retrieval. It also passes A3 in the strongest exposure class
available: a queryable raw banner field with wildcard matching plus port
filtering, so the RFC 4253 prefix predicate is expressible against the bytes the
peer sent rather than against a vendor's service label.

**Six of nine gates pass, one passes with stated bounds, and two are partial.**
A7 stays PARTIAL because the documentation is not silent about its own scanning —
it is silent about exhaustiveness, and inferring exhaustiveness from a list of
enrichment sources would be reading a positive claim out of a negative space.
That is the same refusal for the fourth mission running, and it is the one most
tempting to abandon now that everything else about this apparatus works. A8 stays
PARTIAL on operational questions nobody has asked: retries, duplicate handling
within a window, address-identity counting, and what a missing record means. But
its load-bearing classification is a standard-defined prefix on an exposed banner
rather than a proprietary fingerprint, so what remains unreviewed is operational
rather than semantic — which is the difference from the dropped apparatus.

**The blockers changed kind.** They are no longer about what the apparatus
measures or how it exposes it. Both close by reading or asking, not by finding a
different scanner.

**No partner reached pair analysis, and the reason is recorded honestly.** Three
candidates were probed and all three failed at A6: their first-party technical
documentation was not retrievable at the paths tried. That is a fact about this
mission's reach and not a finding about those apparatuses. The asymmetry is in
documentation access, not apparatus quality, and the record states what the
search does not establish — that no qualifying partner exists.

**The outcome fits imperfectly and the record says so**, rather than choosing the
label whose wording bends most easily. Outcome G is defined for a promising pair
and there is a promising anchor. It was still chosen because it names the
established blocker rather than the merely unexplored one, and because no partner
can rescue an anchor whose own lineage is unproven — while the alternatives would
either assert the anchor qualifies or call an unproven negative a refutation.

**The requirement registry is the reusable output.** Nine rules from Missions 1.47
to 1.59 now sit in one record with the mission that paid for each:
SOURCE_EXCLUSIVE_METRIC, RELIABILITY_REVIEWABILITY, FRAME_INSIDE_THE_DEFINITION,
AFFIRMATIVE_LINEAGE_REQUIRED, PRODUCT_RELEVANCE,
READING_A_PUBLISHED_VALUE_IS_NOT_MEASURING_IT, OBSERVATION_ADDRESSABLE_EXPOSURE,
THE_TEMPORAL_OBJECT_TEST and SAMPLING_IS_LOAD_BEARING. Every one was learned after
a pair had been chosen, which is exactly why they are now applied before.

**Two small rules were made structural.** A query returning only a count still
returns a measurement value, and is not metadata because only a number came back.
A zero-cost trial destroys preregistration exactly as a paid one would, because
access cost is irrelevant to epistemic contamination.

**A falsifiability trap was caught before it mattered.** A windowed count makes
host membership an existential within the window, which looks monotone. The claim
is a count against a bound, which a lower count contradicts. Host-level
monotonicity is not claim-level monotonicity, and conflating them would have
invented a falsifiability problem or hidden one.

10 of 15 first-party documentation retrievals, 0 queries executed, 0 counts, 0
host records, 0 facets, 0 trials, 0 purchases. 0 canonical mutations, 0 sources
registered, 0 governance reviews, 0 collectors, 0 threshold registrations, 0
Claims, 0 Evidence, 0 reliability values, 0 independence groups, 0 Scores, 0
Opportunity changes, 0 model calls, 0 embeddings. The Mission 1.56 Claim is
untouched, the profile is still UNCALIBRATED and Problem-Family is still PARKED.
Validator probed with 85 deliberate violations and 85 caught. 1529 bare-python
tests before commit and 3310 pytest tests after.

New: `docs/data/observation-addressable-scanner-selection-baseline-v1.json`,
`observation-addressable-apparatus-contract-v1.json`,
`anchor-scanner-requalification-v1.json`,
`observation-addressable-partner-candidates-v1.json`,
`observation-addressable-scanner-pair-selection-v1.json` and their rendered `.md`;
`infrastructure/scripts/render_scanner_pair_selection.py`; 36 tests in
`packages/inferred-claim-evaluator/python` and 5 in
`packages/evidence-aggregation/python`.

Report: `docs/architecture/mission-1.60-report.md`.

## 1.92 — 2026-09-05 (Sprint 1 / Mission 1.59)

**`SNAPSHOT_TIME_SEMANTICS_NOT_ALIGNABLE`.** The internet-wide scanning pair
Mission 1.58 found is dropped, on a gate that is not about scanning at all. The
class survives, and so does most of the work.

**The two apparatuses publish different kinds of temporal object.** One is a
stream of observations, each carrying a documented `scan_date` recording when the
scanning that generated it occurred. The other is a maintained current state
whose searchable time field records when a record last *changed*, with the
per-service observation time documented as unsearchable because observation
timestamps change too fast to publish.

**The deciding evidence is the vendor's own worked example.** A host observed
every day for five days without change carries a searchable last-updated
timestamp from five days ago. So the same window filter selects hosts whose
record changed during the window on one side and hosts observed during it on the
other — two different populations. A host present and unchanged throughout is in
one set and missing from the other, and a contradiction produced that way would
be an artefact recorded as a finding, which is the worst failure available to
this layer.

**FAIL rather than UNKNOWN, and the distinction is earned.** The named cadence
document Mission 1.58 could not retrieve was pursued and answered. This is an
established mismatch on first-party documentation from both sides, not a document
nobody found.

**All four alignment rules were evaluated and all four refused**, including the
two that would have salvaged the route. A pre-frozen tolerance was refused
because a tolerance needs an operational basis and the merged side publishes no
bound on how stale a member of its current state may be — any delta would be a
round number chosen precisely because it rescues the route.
Snapshot-inside-interval was refused because establishing it requires per-host
timelines, which means retrieving the set and inspecting it afterwards.

**Three gates that passed a mission ago now read worse, and that is the audit
working.** Population reopened on a disclosure that was there to be read: under
high service density one side's service data represents a sampling rather than a
census, so a partial frame must not be called internet-wide. Reliability
reviewability reopened because the narrowed metric turns on how each side decides
a wire-level predicate and one side's fingerprinting is proprietary. Threshold
freezability fell as a consequence of gate 5.

**What survives is worth more than the pair.** A protocol-native construct now
exists, written source-free: hosts that answer with an identification string
beginning `SSH-` before any negotiation, fixed by RFC 4253 §4.2, which also
states that other server output must not begin with that prefix. No vendor
taxonomy, and matching vendor labels are explicitly refused as metric
equivalence. The narrowing also removes a shared upstream nobody had noticed: a
version- or vulnerability-flavoured metric would have pulled one CVE database
into the load-bearing path on both sides.

**A new apparatus requirement is added: `OBSERVATION_ADDRESSABLE_EXPOSURE`.** An
apparatus qualifies only if a future observation can be attributed to a defined
window from its published surface, before any value is retrieved. That is not the
same as scanning often, and Mission 1.58 could not have known to ask for it. The
generalisable diagnostic behind it: a dataset can be excellent and still be the
wrong temporal object.

**Gate 10 was advanced rather than closed, and only for the side that survives.**
Apparatus B's provenance moved from an absence of any third-party reference to a
positive statement about the load-bearing records, and is still short of an
affirmative denial, so it stays PARTIAL. Apparatus A's lineage was not pursued
further because gate 5 had already dropped the pair, and saying so is better than
reporting an unfinished check as a finished one.

0 measurement endpoints called, 0 measurement values fetched, 0 paid access, 0
trials — load-bearing, because PREREGISTERED is defined against retrieval. 8 of
12 first-party documentation requests used, every load-bearing one first-party. 0
canonical mutations, 0 sources registered, 0 governance reviews, 0 collectors, 0
threshold registrations, 0 Claims, 0 Evidence, 0 reliability values, 0
independence groups, 0 Scores, 0 Opportunity changes, 0 model calls, 0
embeddings. The Mission 1.56 Claim is untouched, the profile is still UNCALIBRATED
and Problem-Family is still PARKED. Validator probed with 77 deliberate
violations and 77 caught — one escaped on the first run, a sentence conflating
structural non-republication with apparatus lineage, and the validator was
tightened rather than the record loosened. 1488 bare-python tests before commit
and 3310 pytest tests after.

New: `docs/data/internet-wide-service-presence-gate-closure-baseline-v1.json`,
`-metric-definition-v1.json`, `-time-contract-v1.json`, `-lineage-review-v1.json`,
`-route-gate-closure-v1.json` and their rendered `.md`;
`infrastructure/scripts/render_service_presence_route.py`; 32 tests in
`packages/inferred-claim-evaluator/python` and 3 in
`packages/evidence-aggregation/python`.

Report: `docs/architecture/mission-1.59-report.md`.

## 1.91 — 2026-09-05 (Sprint 1 / Mission 1.58)

**`PRODUCT_RELEVANT_INDEPENDENCE_CLASS_IDENTIFIED_GATES_OPEN`.** The operator
withdrew Mission 1.57's selected route, made product relevance a mandatory gate,
and the broadened search found the one apparatus class that satisfies the full
conjunction: a world quantity, two documented independent apparatuses, and a real
Opportunity dimension. No route in it qualifies yet.

**A withdrawn selection is appended to, never edited away.** Mission 1.57's
record still reads `selected_route: ROUTE-A`, with the withdrawal recorded beside
it, because deleting the field would lose what the operator decided against —
which is the entire content of the decision. The validator refuses a supersession
that removed it.

**A rule change is not a correction.** Mission 1.57's reasoning was sound under
the rule it was given: its brief listed subject relevance under preferences and
omitted it from the selection rule, and the mission flagged that exact
reservation before asking for approval. Filing a sound analysis as an error would
misdescribe both the analysis and the decision, so the record says which it was.

**Gate 16, `PRODUCT_RELEVANCE`, is mandatory and its cost is stated.** The
construct must bear on a named Opportunity dimension. That narrowing intersects
Mission 1.57's own law directly — product-relevant quantities are overwhelmingly
platform-mediated, and platform-mediated quantities are measured once — so an
empty conjunction was the honest possibility going in.

**Seven classes surveyed, one survives.** Package downloads, business registers
and app-store catalogues are source-exclusive. Web-crawl technology surveys are
`FRAME_INSIDE_THE_DEFINITION` again: each crawler defines its own site
population, and one takes its origin list from a single platform's dataset, so
the frame has a common upstream even where the crawling is independent. Job
postings against official vacancy statistics are genuinely independent producers
of two different constructs — a vacancy is not a posting.

**A new trap, found by certificate transparency.**
`READING_A_PUBLISHED_VALUE_IS_NOT_MEASURING_IT`: several independent log
operators carrying the same submitted certificate are many copies, not many
witnesses. Its test is the sharpest this arc has produced — if the two
apparatuses disagree, is that a fact about the world or a bug? For two readers of
one published number a disagreement is a bug; for two scanners probing the
internet it is a real difference in coverage, timing or fingerprinting, which is
exactly what independent corroboration is supposed to tolerate.

**The surviving class is internet-wide active scanning, and its independence
argument is structural rather than documentary.** Population figures have an
upstream producer, so everyone else distributes. Host counts have none, because
nobody publishes how many hosts run a service — each apparatus must generate the
number by probing. The failure mode that killed World Bank plus FRED, World Bank
plus Eurostat and every platform pair is not merely absent here, it is
structurally unavailable, and that argument cannot be undone by one party
changing its data-sourcing policy.

**The law is refined rather than refuted.** A quantity is independently
measurable exactly when no party is in a position to publish it authoritatively,
and the internet as a whole is such a quantity even though every host on it
belongs to somebody.

**No route was selected, and that is the point.** Twelve of sixteen gates pass
and the set is conjunctive, so selecting the best route found is not selecting
one that qualifies — and the operator asking for a broadened search is not a
reason to lower the bar. Three gates are open, each naming how to close it: gate
3, because vendor fingerprinting is proprietary and the construct must be
narrowed to what the protocol defines or it becomes the CPI-basket failure in a
new domain; gate 5, because two snapshot censuses of a continuously changing
population need a shared reference window and one side's cadence article was not
retrievable; gate 10, because one apparatus states its provenance affirmatively
and the other only by omission — and an absence of a reference to third-party
data is an absence rather than a statement, which is Mission 1.57's own
correction applied rather than forgotten.

**The next mission is epistemics before governance**, inverting Mission 1.57's
recommendation: there the epistemics were closed and only a review remained; here
gate 5 decides whether the two apparatuses measure one proposition at all, and
buying a licence first would be paying to discover a semantic problem.

0 research-data requests, 8 first-party documentation requests, 0 measurement
values fetched — load-bearing, because PREREGISTERED is defined against retrieval
and one value would destroy it permanently. 0 canonical mutations, 0 sources
registered, 0 reviews created, 0 collectors, 0 threshold registrations, 0 Claims,
0 Evidence, 0 reliability assessments, 0 independence groups, 0 Scores, 0
Opportunity changes, 0 model calls, 0 embeddings. The Mission 1.56 Claim is
untouched, the profile is still UNCALIBRATED and Problem-Family is still PARKED.
Validator probed with 103 deliberate violations and 103 caught, 1453 bare-python
tests before commit and 3310 pytest tests after.

New: `docs/data/apparatus-search-broadened-v1.json` and its rendered `.md`; the
supersession appended to `independence-capable-route-feasibility-v1.json`; 14
further tests in `packages/evidence-aggregation/python`.

Report: `docs/architecture/mission-1.58-report.md`.

## 1.90 — 2026-09-05 (Sprint 1 / Mission 1.57)

**`INDEPENDENCE_CAPABLE_ROUTE_GOVERNANCE_PENDING`.** One apparatus pair passes
every mandatory epistemic gate on first-party documentation from both sides.
Neither apparatus is a registered source, so governance is the sole binding
blocker, and it is an unasked question rather than a refusal.

**The structural finding is the mission.** A quantity that exists only because a
platform recorded it can be measured only by that platform; a quantity that
exists in the world independently of any measurer can be measured by more than
one apparatus. Every source in this portfolio measures the first kind. Wikimedia's
request counts exist because Wikimedia's servers logged them; Stack Overflow's
question counts because Stack Overflow published them; GDELT's frequencies because
GDELT crawled and counted; TED's totals because contracting authorities filed
notices there. Each is the sole possible apparatus for its own quantity, so a
second API, dump, mirror or dashboard is a second copy and never a second
measurement. It generalises Mission 1.46 one domain over: there the measurement
happens once at the national producer and the international publishers are
distribution layers; here it happens once at the platform and every interface is
one. Two findings, one fact about where measurement actually occurs.

**Ten held apparatuses, one shared subject, and it is the same one Mission 1.47
found.** `docker`, observed by Wikimedia requests and Stack Exchange questions.
The pair is `COMPLEMENTARY_NOT_CORROBORATING`: a content request is what a
reader's client makes of a server, a published question is what a person writes
about being stuck. ADR-036 removed the identity blocker that stopped those two
ever reaching one Claim; it did not make a request a question.

**The negative controls were re-run and still fail**, which is the one way this
mission could have gone wrong. World Bank plus FRED remains dependent
republication on FRED's own source code; World Bank plus Eurostat remains common
upstream and semantic mismatch. Neither was promoted on the grounds that the
Claim architecture changed, because the INFERRED layer fixes identity and repairs
neither provenance dependence nor a 1 January stock measured against a midyear
estimate.

**The selected route is an atmospheric mole-fraction pair at one fixed site, and
the decisive evidence is a calibration scale rather than an organisation chart.**
The two programmes report on different reference scales, and a republished series
carries the originator's scale. One states first-party that it operates an
independent sampling network rather than obtaining data from the other; the other
describes that data as independent and uses it for comparison, and comparison for
validation is not consumption. Separate instruments, separate laboratories,
separate scales.

**Provenance independence is not error independence, and the limitation is
recorded.** The two share the site and one provides in-kind field support, so a
site-level artefact would move both. The scale offset also becomes a threshold
constraint: a bound placed close enough for a calibration difference to decide the
comparison would manufacture a contradiction, so the next mission must place it
clear of that offset and record the reasoning before any value is retrieved.

**The validator caught this mission's own record.** The rejected web-traffic route
was first written `KNOWN_INDEPENDENT` with no documentary basis. §15 requires the
proof from both sides, so it became `UNKNOWN` — which costs nothing, because that
route fails for a better reason: each apparatus measures share within its own
network, both stating so first-party, so the frame sits inside the metric
definition and any proposition admitting both relocates source attribution into
its predicate. Mission 1.47's finding recurring, now named as the
`FRAME_INSIDE_THE_DEFINITION` trap.

**No measurement value was fetched, and that is load-bearing.** PREREGISTERED is
defined against retrieval, so one value fetched during feasibility work would have
made an honest preregistration impossible for ever afterwards. Research-data
requests 0, first-party methodology requests 6, measurement values 0.

**The reservation is stated rather than buried.** The selected construct is not a
quantity this product will research. Relevance is a preference in the brief and
not a mandatory gate, so selection is permitted; what the route can establish is
that the aggregation mechanism works on real independent data, not what its
parameters should be for a request count. Inside this portfolio there is no
alternative, and that is the finding rather than a gap in the search.

0 canonical mutations across every counter, 0 sources registered, 0 reviews
created, 0 collectors, 0 normalizers, 0 threshold registrations, 0 Claims, 0
Evidence, 0 reliability assessments, 0 independence groups, 0 Scores, 0
Opportunity changes, 0 model calls, 0 embeddings, the Mission 1.56 Claim
untouched, profile still UNCALIBRATED, Problem-Family still PARKED, validator
probed with 79 deliberate violations and 79 caught, 1439 bare-python tests before
commit and 3310 pytest tests after.

New: `docs/data/independence-capable-route-baseline-v1.json`,
`independence-capable-apparatus-requirements-v1.json`,
`independence-capable-route-candidates-v1.json`,
`independence-capable-route-feasibility-v1.json` and their rendered `.md`;
`infrastructure/scripts/render_independence_route.py`; 39 tests in
`packages/evidence-aggregation/python`.

Report: `docs/architecture/mission-1.57-report.md`.

## 1.89 — 2026-09-05 (Sprint 1 / Mission 1.56)

**`FIRST_DETERMINISTIC_INFERRED_CLAIM_PERSISTED`, and the evaluator said
CONTRADICTS.** One attended write, approved by an operator against a frozen
manifest hash, and the first canonical INFERRED Claim this repository holds.
Signal `064d12bf` measured 912 requests against a bound of 1000, so the
proposition is refuted by its own witness -- and that is the pilot succeeding
rather than failing, because the manifest declared all four evaluator results
legitimate before the evaluation ran.

**The repository's first CONTRADICTS Evidence row.** Mission 1.48 measured 57
Evidence rows, found every one SUPPORTS, and established why: `direction` is
proposition identity at the OBSERVED layer, so an interpreter there cannot emit a
contradicting row about a Claim it already restated. ADR-036 removes direction
from identity at the INFERRED layer, and the direction census now reads
`SUPPORTS 57, CONTRADICTS 1`. **The contradiction CASE is still unreached**, and
both halves are reported together: contradiction enters the arithmetic when one
Claim carries evidence in both directions, `claims_carrying_both_directions` is
still 0, and this proposition can never acquire a second witness because only
Wikimedia's own logs can measure requests to a Wikipedia article.

**The approval is a hash, and that is what makes it name a document.** The
operator typed `APPROVE MISSION 1.56 PILOT <sha256>`; the runner recomputes the
hash and refuses anything else, proven by a run against a wrong hash that wrote
nothing. **The manifest was NOT edited afterwards** -- marking it APPROVED would
change its bytes and therefore its hash, so a frozen document that no longer
answers to the hash it was frozen at is not frozen. The validator now REFUSES any
manifest status but `AWAITING_OPERATOR_APPROVAL` for that reason, and the CI gate
re-checks the recorded hash against the manifest on disk, so a later edit turns
the gate red instead of leaving "approved" beside a document nobody approved.

**PREREGISTERED was not merely unavailable, it was arithmetically impossible, and
that is executed rather than argued.** The measurement was retrieved at
`2026-09-01T21:03:47Z`, read from `acquisition.raw_records`; the bound could not
be recorded before today. A test hands the real evaluator a PREREGISTERED
registration with exactly these timings and gets `UNKNOWN /
PREREGISTRATION_TIMING_INCONSISTENT`. POST_HOC is the only representable
classification, the bound sits ABOVE the measurement so the pilot cannot be read
as fitted, and the disclosure that the value was visible when the bound was
chosen is written into the manifest rather than left out of it.

**The bound was committed before the evaluator was constructed.** Registering a
threshold on the way past would be the analyst choosing the number while the
comparison is running, so phase A commits and phase B reads the row that exists.

**Idempotency is demonstrated, not promised.** The whole evaluation and
persistence replayed: status `REUSED`, 0 rows created, every counter identical.
The envelope was checked before and after against what the manifest authorised:
`threshold_registrations +1`, `claims +1`, `claim_revisions +1`, `evidence +1`,
`claim_derivations +1`, `proposition_evaluation_refusals +0`, and every other
counter unchanged.

**The new scope reaches no reviewed reliability, and the near miss is the test.**
Through the REAL resolver, over all four current assessments and their real basis
rows: `NO_APPLICABLE_ASSESSMENT`. The reviewed Wikimedia `0.65` shares source,
resource and record kind, and differs on `claim_type` AND `proposition_kind` --
both differences real, because a threshold proposition is a different question
from a restatement of the count and an INFERRED derivation is a different
question from an OBSERVED one. The Evidence is `NON_SCORABLE`, aggregation is
`UNAVAILABLE`, and that is the designed behaviour rather than a gap.

**A pre-existing defect surfaced and was repaired rather than masked.**
`test_ted_operator_acceptance.py` ran `fetchone()` with no `ORDER BY` over the
two acceptance rows Mission 1.46 left behind and pinned review version 2, so it
passed or failed on row order. It now asserts the property over every row and
that no two review versions share a `verifier_version`, which is what a replay of
an older acknowledgement would look like.

0 network requests, 0 model calls, 0 embeddings, 0 acquisitions, 0 sources added,
0 ReliabilityAssessments created, 0 independence groups, 0 Scores, 0 Opportunity
changes, no migration, evaluator and orchestrator untouched, profile still
UNCALIBRATED, Problem-Family still PARKED, validator probed with **76 deliberate
violations and 76 caught** (each checked to have been refused by its own gate
rather than by the hash check), **1400 bare-python tests before commit** and 3310
pytest tests after.

New: `docs/data/first-deterministic-inferred-pilot-candidate-selection-v1.json`,
`-equivalence-v1.json`, `-manifest-v1.json`, `-v1.json`, `-resolution-v1.json`
and their rendered `.md`; three scripts under `infrastructure/scripts/`
(`render_inferred_pilot.py`, `run_inferred_pilot.py`,
`report_inferred_pilot_resolution.py`); 46 tests in
`packages/inferred-claim-evaluator/python`.

Report: `docs/architecture/mission-1.56-report.md`.

## 1.88 — 2026-09-05 (Sprint 1 / Mission 1.55)

**`DETERMINISTIC_EVALUATION_PERSISTENCE_ORCHESTRATION_READY`, with readiness
reported in two halves rather than collapsed.** One command routes an
EvaluationOutcome to exactly one of two persistence paths inside the caller's
transaction: a directional outcome writes Claim, ClaimRevision, derivation and
Evidence together or not at all, a refusal writes one row and nothing else.
Foundation ready TRUE, unattended production ready FALSE, and 0 canonical rows
written.

The target proposition is passed alongside the outcome, and that is a finding
rather than a signature preference. A refusal carries no proposition key and no
Claim draft by the evaluator's own contract, because it declines to name a
proposition it just declined to establish, while migration 0035 requires the key
and its preimage. The caller supplies the target it already chose: the target is
an input, not something the evaluation concluded.

The Claim statement is composed from the target and nothing else, and that is
where the multi-witness architecture is actually decided. `_persist_one` appends
a revision whenever the statement differs, so a statement naming the witness or
the measurement would make every additional Signal look like a reformulated
Claim. Proved: two witnesses reach one Claim, one revision, two Evidence rows and
two derivations, and a support plus a contradiction reach one Claim with opposite
Evidence directions.

Idempotency means same identity AND same payload. A matching unique key with a
different payload is a conflict, not a replay, for the Claim, the derivation and
the refusal alike. `evaluator_version` is excluded from the derivation comparison
deliberately: the identity excludes it too, so rebuilding the software is not a
new derivation, while reaching a different conclusion under the same rule version
is a finding.

Policy D selected option A: persist the new derivation, leave Evidence untouched,
return REVIEW_REQUIRED. Rolling the re-evaluation back would discard the finding
the reviewer is being asked about. Detection is not re-implemented; Mission 1.41's
`_persist_evidence` already refuses to overwrite a disagreeing relation, and the
orchestrator turns that finding into a result. The conflict is reconstructible
from durable rows by an exact join, and no row declares it a conflict, which is
exactly why unattended readiness is false.

Every rollback is verified through a separate connection, because a read inside
the aborted transaction sees its own uncommitted work. The deferred evidence
trigger is forced rather than assumed.

Two deviations are stated rather than buried: the derivation lands after Evidence
because the canonical Claim API owns its internal ordering, and the aggregator was
not re-run because the aggregation suite has no database and running it upstream
would breach the boundary the brief itself sets. Concurrency is untested and its
behaviour recorded: the loser of a race hits the UNIQUE constraint and rolls back,
which is safe and not graceful.

0 requests of every kind, 0 model calls, 0 embeddings, every counter unchanged, 0
canonical INFERRED Claims, 0 production derivation, refusal or threshold rows, no
migration, evaluator untouched, `validate_claims.py` untouched, profile still
UNCALIBRATED, Problem-Family still PARKED, validator probed with 71 deliberate
violations and 71 caught, 1354 bare-python tests before commit and 3308 pytest
tests after.

New: `services/nlp/python/sros_nlp/inferred_persistence.py`,
`docs/data/deterministic-evaluation-persistence-orchestration-v1.json` and `.md`,
one script under `infrastructure/scripts/`, and 35 transactional tests in
`services/nlp/python`.

Report: `docs/architecture/mission-1.55-report.md`.

## 1.87 — 2026-09-05 (Sprint 1 / Mission 1.54)

**`REFUSAL_PROVENANCE_SCHEMA_IMPLEMENTED`.** Migration 0035 creates the one
additive table ADR-038 froze, `research.proposition_evaluation_refusals`, and
touches nothing else. Additive only, no backfill, no data migration, zero
existing rows changed and zero production rows created.

The three properties the design rests on are proven against real rows rather
than inspected as DDL. A real interpretation run with a bounded expiry and a real
input row naming the same Signal were inserted, a refusal was inserted
independently, and the run was deleted through the ordinary mechanism: the inputs
cascaded to zero and the refusal survived. Deleting the cited Signal alone raises
a foreign key violation, and so does deleting a threshold registration a refusal
judged. A real disposable workspace holding all four kinds of row was then
deleted in one statement and committed, with no deferred-constraint failure and
the refusal removed with its tenant.

Every member of the identity key is NOT NULL, which is what makes it real rather
than nominal: Mission 1.53 proved a UNIQUE containing a nullable column admits
unlimited duplicates. No sentinel and no expression index were needed, because
the equivalence basis is NOT NULL on a measured contract fact rather than a
convenience.

One stricter check was considered and rejected on a measurement. Requiring every
fact value to be a JSON string was enforceable and would have made the table
unable to represent a refusal about the procurement family, whose notice ids and
classification codes are arrays of strings on six live Claims. Only 37 of 43
would have passed. That also corrects an overstatement in the Mission 1.53
design record, which listed flat string values as holding on every live Claim.

The seven reason codes were read from the evaluator's own refusal calls via the
AST and compared pair for pair against ADR-038 before the migration was written.
Zero invented, zero renamed. The pairing check stops a row asserting a shape no
gate produces, and the two vocabulary checks are kept alongside it so a violation
names the actual defect.

Two false positives in the new validator were repaired structurally rather than
by loosening: the identity check first matched a comment quoting the other
table's key, and the untouched-trigger check first matched the paragraph headed
WHAT IS NOT TOUCHED. And a defect written in Mission 1.53 surfaced here: that
mission re-pointed a database test for pinning a migration head, then wrote a
head pin into its own validator and its own test suite. Both are now the property
they were protecting, that 0034 is still present.

The leak check went 28 to 29 tenant tables and validate_schema reports 46, both
picking the table up automatically. Two pinned lists needed extending, which is
what a new table costs.

0 requests of every kind, 0 model calls, 0 embeddings, every counter unchanged,
0 INFERRED Claims, 0 derivation rows, 0 threshold registrations, 0 production
refusal rows, evaluator untouched, claim_derivations untouched, trigger
untouched, profile still UNCALIBRATED, Problem-Family still PARKED, validator
probed with 70 deliberate violations and 70 caught, 1354 bare-python tests before
commit and 3273 pytest tests after.

New: `infrastructure/db/migrations/0035_refusal_provenance.sql`,
`docs/data/refusal-provenance-schema-v1.json` and `.md`, one script under
`infrastructure/scripts/`, and 72 database tests in `services/nlp/python`.

Report: `docs/architecture/mission-1.54-report.md`.

## 1.86 — 2026-09-05 (Sprint 1 / Mission 1.53)

**`INPUT_KEYED_REFUSAL_PROVENANCE_MODEL_SELECTED` (ADR-038).** A refusal gets its
own append-only record, keyed on the input witness, the candidate target
proposition, the derivation rule version and the reviewed equivalence basis. It
names no ClaimRevision, creates no Claim, produces no Evidence, and needs no
change to claim_derivations, to the evidence-requirement trigger, or to any
existing schema. No migration was created and no table exists.

Option B was measured rather than dismissed, and it fails on a fact only a live
probe produces. A temp table mirroring claim_derivations_identity_key accepted
three identical rows with a NULL claim_revision_id, and refused the duplicate the
moment the column was populated. PostgreSQL treats NULLs as distinct, so making
that column nullable silently removes the table's only idempotency guarantee from
exactly the rows the change exists to add. Its second failure is quieter:
claim_derivations identifies its proposition only through claim_revision_id, so
with that NULL the row cannot say what was refused.

Migration 0034 had already anticipated refusals. Its threshold-required check
makes the registration optional precisely for the two refusal results, and its
result check admits all four. Two constraints written in one migration disagree
with each other, which is the finding rather than a tie-breaker.

The candidate target is stored as a key and its exact preimage, in the vocabulary
research.claims.proposition_facts already uses. Measured: all 43 live Claims
carry both, the discriminator key is `proposition` on all 43, and the evaluator
already emits it, so a refusal and the Claim it may later become are comparable
by key. The key is recomputable, so it is verifiable rather than trusted.

The seven reason codes were read from the evaluator's own refusal calls via the
AST, and none was invented or renamed. The equivalence basis is NOT NULL because
the decision contract already requires a non-blank basis id for every verdict,
which also keeps the identity key free of nullable columns. A changed basis
creates a new historical row rather than updating an old one, and a later
SUPPORTS leaves an earlier UNKNOWN entirely alone.

One deviation from the brief is flagged rather than buried: the descriptor
carries no schema version, because derivation_rule_version already pins which
fact set was emitted and a second version field would be a second authority for
one fact. Recorded as OPERATOR_REVIEWABLE_DEVIATION with its cost stated.

Two testing traps were caught. The evidence-requirement trigger is deferrable, so
a rollback fixture never fires it and the first version of the test reported a
pass for a rule that never ran. And the new pytest classes were first named
without a Test prefix, which collected zero tests silently.

0 requests of every kind, 0 model calls, 0 embeddings, every counter unchanged,
0 INFERRED Claims, 0 derivation rows, 0 threshold registrations, no migration,
validate_claims.py untouched, profile still UNCALIBRATED, Problem-Family still
PARKED, validator probed with 66 deliberate violations and 66 caught, 1354
bare-python tests before commit and 3201 pytest tests after.

New: `docs/architecture/adr/ADR-038-refusal-provenance-binding.md`,
`docs/data/refusal-derivation-binding-baseline-v1.json`,
`docs/data/refusal-derivation-binding-design-v1.json` and `.md`, one script under
`infrastructure/scripts/`, 41 design tests in
`packages/inferred-claim-evaluator/python` and 15 database tests in
`services/nlp/python`.

Report: `docs/architecture/mission-1.53-report.md`.

## 1.85 — 2026-09-05 (Sprint 1 / Mission 1.52)

**`REFUSAL_DERIVATION_BINDING_CONTRACT_GAP`, with
`DETERMINISTIC_EVALUATOR_FOUNDATION_IMPLEMENTED` reported beside it.** The
deterministic evaluator exists, runs and refuses correctly. What it cannot do is
write a refusal down.

Proven in a disposable probe workspace rather than reasoned about: an INFERRED
claim with no Evidence is refused by the evidence-requirement trigger, whose
exemptions are HYPOTHESIS, MANUAL and WITHDRAWN and nothing else; and a
derivation with a NULL claim_revision_id is refused by migration 0034. Both
refusals are individually correct, and jointly they leave a NOT_APPLICABLE or
UNKNOWN evaluation nowhere to store its provenance without first fabricating the
Claim the evaluation just declined to establish. Nothing was widened to get past
it: INFERRED was not added to the exemptions, claim_revision_id was not made
nullable, no Claim was created and no table was invented.

The Evidence re-evaluation question resolves by policy instead, and the
distinction is why the first is the primary outcome. `scoring.evidence` has no
revision or supersession column, so a rule-version change produces another
derivation record, never an automatic alteration of canonical Evidence, and a
disagreement is reported for operator review. That needs no schema change; the
refusal gap needs a decision nobody has taken.

`packages/inferred-claim-evaluator` sits at the path ADR-037 Q3 named and joins
the zero-dependency runner with one named shared package rather than the
monorepo. Four gates run in order, equivalence first, so the direction the
arithmetic would have produced cannot leak into a refusal. No unit is converted,
no time window aligned, no threshold selected, no independence adjudicated, no
reliability scored, and interpretation confidence is taken from the reviewed
equivalence decision rather than invented.

The aggregator needs no change, proved from its signature: `aggregate()` takes no
claim type and `EvidenceItem` carries none. A correction was made in the process
— EvidenceDirection does have a NEUTRAL member, so the guarantee that a refusal
never becomes NEUTRAL is producer-side rather than type-side, and the record says
so rather than repeating the mistake.

0 requests of every kind, 0 model calls, 0 embeddings, every counter unchanged,
0 INFERRED Claims, 0 derivation rows, 0 threshold registrations, no migration,
`validate_claims.py` untouched, profile still UNCALIBRATED, Problem-Family still
PARKED, validator probed with 55 deliberate violations and 55 caught, 1313
bare-python tests run before commit and 3186 pytest tests after.

New: `packages/inferred-claim-evaluator/`,
`docs/data/deterministic-inferred-evaluator-foundation-v1.json` and `.md`, one
script under `infrastructure/scripts/`, and a downstream compatibility suite in
`packages/evidence-aggregation/python`.

Report: `docs/architecture/mission-1.52-report.md`.

## 1.84 — 2026-09-04 (Sprint 1 / Mission 1.51)

**`DETERMINISTIC_DERIVATION_PROVENANCE_SCHEMA_IMPLEMENTED`.** Migration 0034
creates the two additive records ADR-037 froze: `research.threshold_registrations`
and `research.claim_derivations`. Additive only, no backfill, no data migration,
zero existing rows changed and zero production rows created.

The load-bearing proof is a DELETE rather than a sentence. A real interpretation
run with a bounded expiry and a real input row naming the same Signal are
inserted, a durable derivation is inserted independently, the run is deleted
through the ordinary mechanism, and both are re-read: the inputs cascaded to zero
and the derivation survived. Deleting a Signal cited by a derivation raises a
foreign key violation, so retention cannot silently take the reasoning with it.

The deferrable finding was found by the database rather than by reasoning. The
foreign keys were first plain ON DELETE NO ACTION, on the argument that NO ACTION
is checked at the end of the statement. An undeferred NO ACTION is checked at the
end of each cascading statement, and the cascade removing claim_revisions runs
before the one removing the derivations citing them, so every committing test's
teardown failed. DEFERRABLE INITIALLY DEFERRED moves the check to COMMIT, where a
workspace deletion has removed both sides and a lone Signal purge has not.

The two idempotency keys differ deliberately and a test reads both from the live
schema to pin it. Derivation records are append-only with no supersession column,
bound to the ClaimRevision. Threshold provenance is not Claim identity: the key
includes provenance_status, and the table stores no proposition key, no claim id
and no calibration eligibility, which is derived from status instead.

origin_detail, claims, evidence and both interpretation tables are untouched. The
single ALTER is a semantically vacuous unique constraint on claim_revisions that a
composite tenant-safe foreign key requires.

The pytest leak check now reports the database unchanged across 28 tenant tables,
up from 26, having picked both new tables up automatically.

New: `infrastructure/db/migrations/0034_deterministic_derivation_provenance.sql`,
`docs/data/deterministic-derivation-provenance-schema-v1.json` and `.md`, one
script under `infrastructure/scripts/`, and 28 database tests in
`services/nlp/python`.

Report: `docs/architecture/mission-1.51-report.md`.

## 1.83 — 2026-09-04 (Sprint 1 / Mission 1.50)

**`DETERMINISTIC_INFERRED_CLAIM_CONTRACT_READY`** (ADR-037). The minimum additive
contract for source-attributed OBSERVED inputs, deterministic derivation, and a
source-independent INFERRED Claim. All four mandatory questions resolved, schema
necessity BOTH_REQUIRED and fully specified, and no migration created.

The Claim and the Evidence need nothing new. The reasoning has nowhere durable to
live, and the verdict rests on a measured fact rather than a preference. The
closest existing structure is claim_interpretation_inputs, one row per run and
signal, but all twelve rows of its parent claim_interpretation_runs carry a
populated expires_at about ninety days out and the inputs foreign key is ON
DELETE CASCADE. When a run expires every input row goes with it, so a Claim would
outlive the record of how it was derived.

origin_detail keeps one responsibility. It answers where a Claim came from on all
43 live Claims; a reasoning step answers a different question, and putting both
there is one free-text field answering two independent questions.

Evidence attaches directly, on existing architectural intent: the epistemic
semantics already say an INFERRED claim carries the Signals it reasoned from as
Evidence. No Claim-to-Claim relation is required. Attachment and derivation
provenance are both required and neither substitutes for the other.

Derivation provenance binds to the ClaimRevision, with one rule and many
evaluations, because one prose rationale cannot explain both why one source
supports and why another contradicts. Its idempotency key deliberately differs
from Evidence's: Evidence must not duplicate on a version bump, and a derivation
record must be distinct per rule version.

Threshold provenance is not proposition identity, and never changes entailment.
Preregistration is defined against retrieval rather than publication, and the
rule states that it cannot exclude human foreknowledge.

interpretation_confidence is not a gap. Its documented meaning is confidence that
the wording faithfully states what the Signals showed, which for a deterministic
threshold Claim is confidence in the semantic-equivalence mapping rather than in
the arithmetic. There is no derivation_confidence field and there must not be
one.

The evaluator belongs in a new package that was not created, because hosting it
in the interpreters would require weakening validate_claims.py.

Purely additive. 43 Claims, 44 revisions and 57 Evidence untouched. Zero requests
of any kind, zero model calls, zero embeddings, seventeen counters unchanged,
zero INFERRED Claims and zero migrations.

New: `docs/architecture/adr/ADR-037-deterministic-inferred-claim-contract.md`,
`docs/data/deterministic-inferred-claim-contract-v1.json` and `.md`, one script
under `infrastructure/scripts/`, and tests in `claim-model` and
`evidence-aggregation`.

Report: `docs/architecture/mission-1.50-report.md`.

## 1.82 — 2026-09-04 (Sprint 1 / Mission 1.49)

**`SOURCE_INDEPENDENT_PROPOSITIONS_BELONG_TO_INFERRED_LAYER`** (ADR-036). A
proposition about the world, rather than about a publisher, is an INFERRED Claim.
The layer already exists, it was defined for exactly this, and nobody has built
it.

`claim-epistemic-semantics-v1.md` §4 defines INFERRED as a claim that asserts
something about the world that the measurement is evidence for and that the
source did not itself report. That is the source-independent proposition,
verbatim, written in Mission 1.13. No new ClaimType, no subtype, no migration.

The assumption that INFERRED means model-generated is false, and the taxonomy
refutes it twice. By type, INFERRED is derived analytically while PREDICTED is a
model-generated estimate. By axis, claim_type is the epistemic category and
interpretation_kind is the procedure, and migration 0016's CHECK constraint ties
interpretation_kind to the presence of a model_version rather than to claim_type.
So INFERRED plus DETERMINISTIC is representable today and has never been written.

A cross-source OBSERVED convergence Claim was rejected on the project's own
sentence: an OBSERVED claim that should have been INFERRED is a fabrication with
a citation attached. A new Claim type was found unnecessary rather than wrong,
because interpretation_kind already carries the distinction it would encode.
Deliberate absence was evaluated seriously and rejected because it is not the
conservative option: the layer is already defined, and the unstated cost is that
the system remains unable to say that two sources disagree.

Three exclusions carry the new identity. The measurement value is not proposition
identity, or 110 and 105 would be two Claims. source_id is not identity in the
new layer and remains identity for OBSERVED. Direction is not identity, the exact
inversion of the OBSERVED layer.

Source independence of the proposition is never provenance loss: every witness
keeps source_id and the full chain to RawRecord. Reliability is unaffected
because Claim identity and Evidence reliability scope are different things.
Measurement reliability and derivation validity must never be multiplied. A
threshold must be preregistered, source-native or an external norm to be
calibration-eligible.

Fixtures ran through the real aggregator: two independent supports give two
groups and strength 0.8 against a strongest member of 0.6; a support and a
contradiction on one Claim give contradiction 0.5 and four masses summing to 1.0;
a republication stays one group at 0.6.

Purely additive. 43 Claims, 44 revisions and 57 Evidence keep their identities
and meaning, zero identities rewritten, zero migrations recommended. Zero
requests of any kind, zero model calls, zero embeddings, all sixteen counters
unchanged.

New: `docs/architecture/adr/ADR-036-source-independent-claim-semantics.md`,
`docs/data/source-independent-claim-semantics-v1.json` and `.md`, one script
under `infrastructure/scripts/`, and tests in `evidence-aggregation` and
`claim-model`.

Report: `docs/architecture/mission-1.49-report.md`.

## 1.81 — 2026-09-04 (Sprint 1 / Mission 1.48)

**`CONTRADICTION_CLAIM_IDENTITY_ARCHITECTURE_GAP`.** The contradiction machinery
is fully functional and structurally unreachable, and the fact that blocks it is
the same fact that blocked Mission 1.47.

A non-persisted fixture drives the real aggregator to non-zero contradiction
strength and non-zero conflict mass, with all four masses summing to one. So the
arithmetic is not the gap. All 57 live Evidence rows are SUPPORTS and none has
ever been otherwise.

Nothing was quoted from a mission report. The B-2 identity was re-derived by
running the real aggregator over all 43 live Claims with reliability resolved
through the real resolver, against a B-2 computed independently, giving zero
cases where the two differ and a maximum of one support group per Claim.

Contradiction is blocked three times. Direction is a proposition fact, so an
increase and a decrease are two Claims. EvidenceDirection.SUPPORTS appears
exactly once in the whole interpreters package as a hard-coded literal and
CONTRADICTS appears nowhere. And all 43 Claims carry source_id in proposition
identity, so two publishers reporting incompatible values form two Claims before
their values are ever compared.

That third blocker is the unification. Corroboration needs two observations on
one Claim and contradiction needs two observations on one Claim, so source
attribution in proposition identity closes both roads out of the baseline with
one decision. The binding constraint is therefore not a missing apparatus: a new
apparatus would land on its own Claim and change nothing.

The corpus supplied its own demonstration. Three Claim pairs differ only in
direction, and the most contradiction-looking pair in the repository is not one
for three independent reasons: they are two Claims, they are both true at once,
and a counterexample cannot falsify a monotone existential.

Seven proposition families were evaluated on eight qualitative criteria with no
weighted numeric score. THRESHOLD_STATE is preferred because it serves both
routes, and the cost of the choice is recorded: the threshold is ours, so it must
be frozen before the second measurement is retrieved.

Reliability reviewability is promoted to a first-class search criterion, because
one robots-blocked methodology page disqualified an otherwise strong apparatus on
two separate gates in Mission 1.47.

No source was selected and the apparatus specification names none, enforced by a
validator. Zero requests of any kind, zero model calls, zero embeddings, and all
sixteen counters unchanged.

New: `docs/data/falsifiable-evidence-apparatus-requirements-v1.json` and `.md`,
`docs/data/falsifiability-vs-convergence-tradeoff-v1.json`,
`docs/data/falsifiable-evidence-apparatus-gap-baseline-v1.json`, two scripts
under `infrastructure/scripts/`, and tests in `evidence-aggregation` and
`claim-model`.

Report: `docs/architecture/mission-1.48-report.md`.

## 1.80 — 2026-09-04 (Sprint 1 / Mission 1.47)

**`FORMALLY_VALID_BUT_INFORMATIONALLY_WEAK`.** A narrow, source-faithful
proposition over the Docker subject is independently entailed by both held
apparatuses, and it discards exactly what each of them measures.

An apparatus is `(source, proposition_kind)` rather than a source: four sources
operate nine apparatuses, two of them running two each over one corpus. The
subject overlap was measured across all nine before any pair was considered, and
Docker is the only cross-apparatus shared subject in the held corpus, with
Wikimedia carrying 12 Evidence rows against Stack Exchange's 2, while kubernetes
and podman carry 12 and 0.

The one candidate that passes same-proposition semantics is an existential, and
the only definition of its event class that admits both members is a disjunction
of the two publishers' own mechanisms. So source attribution is not removed but
relocated, from the subject of the sentence into the definition of its predicate.
The first strengthening that would carry information fails twice over, on the
prohibition against normalising unlike quantities and on period alignment.

The Stack Exchange window runs from 2024-03-01T08:06:03Z to 2024-03-05T04:17:20Z
against whole UTC day buckets, so the windows overlap and are not aligned. Both
sit inside March 2024, and containment is weaker than alignment. No monthly
aggregate was manufactured: an existential needs none, and 7 of 31 March days are
held so completeness was not established either.

Five of the eight gates pass. Independence is UNKNOWN and, unlike Mission 1.46's,
is not refuted. Two independent gates fail on one root cause: Stack Exchange's own
methodology documentation is unreachable because the site's robots policy blocks
this environment's fetcher, which leaves its measurement lineage undocumented and
is the same insufficiency for which the operator already declined both Stack
Exchange reliability scopes in Mission 1.36.1.

The convergence contract structurally cannot express a cross-apparatus
proposition, proved through the real constructor: source_id is mandatory in
identity fields and SourceBoundary has exactly one member.

No route was selected and no least-bad fallback was taken. The architecture gap
and the independence gap are recorded as findings rather than as the outcome,
because both sit downstream of the proposition being near-tautological.

Zero requests of any kind, zero model calls, zero embeddings, and every one of
fifteen research counters unchanged.

New: `docs/data/cross-apparatus-convergence-feasibility-v1.json` and `.md`,
`docs/data/cross-apparatus-holdings-baseline-v1.json`, two scripts under
`infrastructure/scripts/`, and
`packages/evidence-aggregation/python/tests/test_cross_apparatus_convergence.py`.

Report: `docs/architecture/mission-1.47-report.md`.

## 1.79 — 2026-09-04 (Sprint 1 / Mission 1.46)

**`COMMON_UPSTREAM_SOURCE_PREVENTS_INDEPENDENCE`.** Neither World Bank + Eurostat
nor World Bank + FRED can produce two established independent provenance groups
over one bounded proposition.

FRED republishes the exact World Bank series already held: its own page names
Source "World Bank", Release "World Development Indicators" and Source Code
SP.POP.TOTL, and its suggested citation credits the World Bank as author and FRED
as the retrieval point. Semantically identical, and dependent for that reason.

Eurostat fails both gates. The World Bank's own indicator metadata names
"Eurostat: Demographic Statistics" as one of four sources for SP.POP.TOTL, and
Eurostat's ESMS metadata states that population data are collected by Eurostat
from National Statistical Institutes under Regulation (EU) No 1260/2013. And the
measurements differ anyway: de facto population at midyear against usually
resident population on 1 January.

The structural finding is that for official macro statistics the international
publishers are distribution layers over national producers, so adding a second
statistical publisher cannot create a second provenance group for a national
aggregate.

No route was selected and no least-bad fallback was taken. No qualified
alternative was named inside the eligible statistical portfolio, because it is
exactly the three publishers that share producers.

The mandatory precondition was completed first: the operator's TED local review
v3 acceptance was recorded through the supported domain API under a new
verifier_version naming the v3 text, with 17 of 17 post-write checks passing and
TED eligible again under local-private-research-v1.

Zero research-data requests, one METADATA_ONLY call persisting no RawRecord, zero
model calls, zero embeddings, and every research counter unchanged.

New: `docs/data/independent-statistical-route-feasibility-v1.json` and `.md`,
`docs/data/statistical-holdings-baseline-v1.json`, two scripts under
`infrastructure/scripts/`, and
`packages/evidence-aggregation/python/tests/test_independent_statistical_route.py`.

Report: `docs/architecture/mission-1.46-report.md`.

## 1.78 — 2026-09-04 (Sprint 1 / Mission 1.45)

**`TED_OFFICIAL_REUSE_GUIDANCE_RECONCILED`.** The Publications Office answered
the clarification request this repository has carried as an unsent draft since
Mission 1.15.3.

Written reply of 2026-09-04 from the Head of Sector for Copyright and legal
issues, case 2026-COP-201, answering a request that described this system by name
as a commercial software-as-a-service application. TED notices and metadata may
be reused for both commercial and non-commercial purposes, provided the source is
acknowledged and according to the copyright notice; whether or not the EU asserts
copyright over the database should not prevent reuse; and the way the data are
retrieved is not relevant in this regard.

H-36A is split rather than answered: database-right EXISTENCE stays
NOT_ESTABLISHED, because the reply says copyright rather than sui generis and
says "whether or not"; whether such a right BLOCKS reuse is
OFFICIAL_FIRST_PARTY_GUIDANCE_INDICATES_NOT_A_BLOCKER. H-36B becomes
RETRIEVAL_METHOD_NEUTRALITY_FOR_REUSE, bounded: not a database-right grant, and
not permission to bypass any technical control.

Questions 4 and 5 of the request received no answer. The scope of "SIMAP's system
metadata" stays UNRESOLVED and no structured notice field is classified CC0. The
COM_REUSE versus CC BY catalogue mapping stays NOT_FULLY_RESOLVED and is
non-blocking.

Local review v2 to v3, commercial v5 to v6, append-only: 255 insertions and 0
deletions. The local verdict stays APPROVED_WITH_CONDITIONS and the commercial
verdict stays REQUIRES_REVIEW, with its blocker changed from H-36 to raw
redistribution, resale and customer-facing access, none of which the request
described.

Appending orphans the operator's 2026-09-01 acceptance by design, so TED is
INELIGIBLE under the local profile until a named operator records it again.

Migration 0033: OPERATOR_CORRESPONDENCE was a permitted evidence type that the
http-only URL rule made unstorable. Correspondence may now address itself by a
mailto locator and must then carry a fingerprint.

Zero research-data requests, zero model calls, zero reliability changes, and no
personal-data field in any of the 188 TED records held.

New: `docs/data/ted-eu-official-reuse-response-v1.md`,
`infrastructure/db/migrations/0033_correspondence_evidence_locator.sql`,
`services/acquisition/python/tests/test_ted_official_reuse_response.py`.

Report: `docs/architecture/mission-1.45-report.md`.

## 1.77 — 2026-09-04 (Sprint 1 / Mission 1.44.1)

**`WIKIMEDIA_CONVERGENT_OPERATOR_RELIABILITY_DECISION_PERSISTED`**, with
**`AGGREGATION_MECHANISM_STILL_UNIDENTIFIABLE_FROM_REAL_CORPUS`** beside it.

The operator typed the confirmation. ReliabilityAssessments 3 → 4, basis rows
10 → 12. Assessment `19e0ce16-…` v1, `0.6`, `HUMAN_REVIEW`, `thibchm`,
`human-reliability-assessment-rubric@1.0.0`. Every other canonical counter
unchanged.

All 18 convergent Evidence rows resolve to that one assessment, and
`scoring.evidence.reliability` stays NULL on all 57. Thirty-six leak checks over
every proposition kind against all four current assessments, zero leaks. The
three historical assessments are untouched and neither pre-rubric row was
backfilled.

Six real multi-Evidence Claims became scorable, and `max(members)` received
**four** real canonical items for the first time, then three four times and two
once. Scorable multi-Evidence Claims 2 → 8, max scorable cardinality 2 → 4.

And the number did not move. `IDENTICAL_TO_RELIABILITY_PASS_THROUGH` on all six,
`q = 0.6` limited by reliability on 34 of 34, EvidenceScore 60.0, level 1 blocked
on established independence. Every Claim forms exactly one unknown-provenance
group, so the full aggregator and the B-2 baseline are the same number
algebraically rather than coincidentally. **Four witnesses is not corroboration.**

No calibration label, no parameter fitted, no Score, no Opportunity change, no
ranking, no embeddings, no network request and no model call. Problem-Family
stays PARKED.

New: `docs/data/wikimedia-convergent-operator-reliability-review-v1.json` and
`.md`, `docs/data/wikimedia-convergent-reliability-resolution-v1.json`, and two
scripts under `infrastructure/scripts/`.

Report: `docs/architecture/mission-1.44.1-report.md`.

## 1.76 — 2026-09-04 (Sprint 1 / Mission 1.44)

**`READY_FOR_WIKIMEDIA_CONVERGENT_RELIABILITY_REVIEW`.** The reliability question
for the convergent Wikimedia proposition kind is prepared and not answered, under
`human-reliability-assessment-rubric@1.0.0`.

18 Evidence rows across 6 Claims with cardinalities {4,3,3,3,3,2}, collapsing to
exactly one five-part scope that resolves `NO_APPLICABLE_ASSESSMENT`.

The almost-match is tighter than TED's: the existing Wikimedia `0.65` shares four
of five scope fields and differs only on `proposition_kind`. Thirty leak checks
over every proposition kind in the corpus, zero leaks.

Software asserted one dimension state and deliberately not the obvious one.
Mission 1.42 could assert `NOT_ESTABLISHED` for TED's mutability because the
basis said nothing; here it says something and not enough — a known-problems list
records an incident and states no revision policy — and that is a judgement about
sufficiency, so `HISTORICAL_MUTABILITY` stays blank.

Nothing was fetched, no assessment or basis row was persisted, and every
canonical counter is unchanged.

A third latent defect of the same shape was found by the §37 fixture requirement:
`ReliabilityBinding.to_json()` crashed on an optional field four generators
already pass as `None`, in a branch the live corpus never reaches.

New: `docs/data/wikimedia-convergent-reliability-review-packet-v1.json` and
`.md`, and `infrastructure/scripts/build_wikimedia_convergent_reliability_packet.py`
with its authored findings input.

Report: `docs/architecture/mission-1.44-report.md`.

## 1.75 — 2026-09-04 (Sprint 1 / Mission 1.43)

**`CALIBRATION_REFERENCE_CORPUS_MEANINGFULLY_EXPANDED`**, with
`NEW_CORPUS_SHAPE_NON_SCORABLE_MISSING_RELIABILITY` beside it.

Measured before any work: 0 of 37 Claims have more than one support group, and 0
show an aggregator result differing from the B-2 reliability pass-through
baseline. With one group that identity is algebraic, so adding single-group
Evidence cannot make them differ. The aggregation layer becomes measurable only
through established independence or contradiction.

A second convergence contract,
`platform-counted-content-request-change-witnessed@1.0.0`, over the 18 Wikimedia
Signals already held. **Zero network requests** — and not merely for economy:
Wikimedia acquisition is blocked by three unsatisfied conditions in this
deployment.

Claims 37 → 43, ClaimRevisions 38 → 44, Evidence 39 → 57, Claims with more than
one Evidence 2 → 8, max Evidence per Claim 2 → 4. Every other counter unchanged.

Another TED division was refused as `TOO_SIMILAR_TO_CURRENT_CORPUS` despite being
immediately scorable. Nothing was manufactured: no contradiction, no
independence, no temporality.

New: `docs/data/calibration-corpus-expansion-plan-v1.json` (frozen in its own
commit before any derivation), `calibration-corpus-baseline-v1.json`,
`calibration-corpus-shape-after-v1.json`,
`calibration-corpus-expansion-run-v1.json`, and two scripts under
`infrastructure/scripts/`.

Report: `docs/architecture/mission-1.43-report.md`.

## 1.74 — 2026-09-04 (Sprint 1 / Mission 1.42.1 close-out)

**`SECOND_PILOT_OPERATOR_RELIABILITY_DECISION_PERSISTED`.** The operator typed
the confirmation. ReliabilityAssessments 2 → **3**, basis rows 6 → **10**, and
thirteen other counters unchanged.

Assessment `d1afa4be` v1, `0.55`, `HUMAN_REVIEW`, `thibchm`, under
`human-reliability-assessment-rubric@1.0.0` — the first assessment that records
which procedure produced it. Both historical assessments keep NULL provenance and
neither is superseded.

All six convergent Evidence rows resolve, and `scoring.evidence.reliability` is
still NULL on all 39: reliability binds late. Nine leak checks, zero leaks.

**Both real multi-Evidence Claims became scorable, 0 → 2**, and `max(members)`
received two real items for the first time — one support group of kind UNKNOWN
with two members, because DISJOINT membership is not independence. Zero
independence groups created.

The result is `IDENTICAL_TO_RELIABILITY_PASS_THROUGH` on both Claims, which is
not a failure: the mechanism ran, and the corpus gives it nothing to disagree
about. `q = 0.55` limited by reliability, masses 0.55/0/0/0.45, EvidenceScore
55.0, level 1 blocked on established independence.

`REFERENCE_PROFILE_V1` remains `UNCALIBRATED`. D-03 blocker 2 → PARTIAL; the
other four unchanged.

Report: `docs/architecture/mission-1.42.1-report.md`.

## 1.73 — 2026-09-04 (Sprint 1 / Mission 1.42.1)

**`OPERATOR_CONFIRMATION_REQUIRED`**, reached with everything else complete.
Migration 0032 adds `review_rubric_id` and `review_rubric_version`, both
nullable; the operator's completed review is frozen as an artifact that conforms
to the rubric it names; and the dry run validates at version 1, `HUMAN_REVIEW`,
`thibchm`, `0.55`, `human-reliability-assessment-rubric@1.0.0`, four
document-backed basis rows.

**0 assessments persisted.** A brief can supply a reviewer's values and cannot
supply their keystroke, and piping the confirmation would produce a row whose
`reviewed_by` names a person who did not type it.

The scope was not narrowed to the second pilot: it carries no classification
division and no currency, so one judgement binds six Evidence rows across four
Claims, divisions 90 and 92, EUR and SEK.

Nothing was backfilled — both historical assessments read NULL, which is true
rather than missing — and the basis table was considered and rejected as the
place for rubric provenance.

Counters unchanged: ReliabilityAssessments 2, basis rows 6, and
`scoring.evidence.reliability` NULL on all 39 rows.

New: `infrastructure/db/migrations/0032_reliability_review_rubric_provenance.sql`,
`docs/data/second-pilot-convergent-operator-reliability-review-v1.json` and
`.md`, `docs/data/second-pilot-convergent-reliability-resolution-v1.json`, and
two scripts under `infrastructure/scripts/`.

Report: `docs/architecture/mission-1.42.1-report.md`.

## 1.72 — 2026-09-04 (Sprint 1 / Mission 1.42a)

**`HUMAN_RELIABILITY_RUBRIC_READY`**, with
`RELIABILITY_RUBRIC_PROVENANCE_MODEL_GAP` recorded beside it.
`human-reliability-assessment-rubric@1.0.0` supplies the step the architecture
never defined: from documented facts to an accountable human judgement, or to a
reasoned refusal to make one.

Five dimensions accepted, six rejected. The rejections carry the boundary:
measurement-to-proposition fit is `directness` and became a hard stop rather than
a dimension; a separate reviewer-confidence field was refused because the
dimension profile already answers it.

UNKNOWN is not LOW structurally — `NOT_ESTABLISHED` and `CONTRADICTED` carry no
ordinal rank — and the module contains no arithmetic operator of any kind.

Scale recommendation: `KEEP_NUMERIC_FIELD_BUT_REQUIRE_ORDINAL_REVIEW_PROFILE_FIRST`.
Two anchors defined by their role in `q = min(components)`, no intermediate
anchors, no migration, and both historical assessments unchanged and
`PARTIALLY_REPRESENTABLE`.

The TED convergent worked example is prepared with every judgement field blank.
No reliability was assigned, suggested or ranged.

Counters: all unchanged. 0 assessments, 0 basis rows, 0 model calls, 0
acquisitions.

New: `docs/data/human-reliability-assessment-rubric-v1.md` and `.json`,
`packages/evidence-reliability/python/sros_evidence_reliability/rubric.py`,
`infrastructure/scripts/render_reliability_rubric.py` with a CI `--check`.

Report: `docs/architecture/mission-1.42a-report.md`.

## 1.71 — 2026-09-04 (Sprint 1 / Mission 1.42)

**`READY_FOR_SECOND_PILOT_RELIABILITY_REVIEW`.** The reliability question for the
convergent TED proposition kind is prepared and **not answered**. 0
ReliabilityAssessments, 0 basis rows, 0 network requests, 0 model calls, every
canonical research counter unchanged.

The brief expected four Evidence rows on two Claims. The live scope holds **six
rows across four Claims**, resolving to exactly one scope, which is exactly the
expected five-part one. That is not scope drift: a reliability scope carries no
classification division and no currency, so it also reaches the SEK claim and the
division-90 claim. One judgement binds all six rows.

The existing TED `0.5` shares four of five scope fields and does not bind, on
`proposition_kind` alone — exercised through the real resolver in both directions
and confirmed by six leak checks with zero leaks. Nothing new was retrieved:
three of four held basis rows are REUSED and BT-195–BT-198 is
PARTIALLY_APPLICABLE, because withholding cannot falsify an existential.

Engineering validation is recorded separately and refused as documentary basis.
Correct currency grain does not imply reliability, and DISJOINT overlap does not
imply independence.

New: `docs/data/second-pilot-convergent-reliability-review-packet-v1.json`,
`docs/data/second-pilot-convergent-reliability-review-packet-v1.md`, and
`infrastructure/scripts/build_convergent_reliability_packet.py` with its
authored findings input.

Report: `docs/architecture/mission-1.42-report.md`.

## 1.70 — 2026-09-03 (Sprint 1 / Mission 1.41)

**`PROCUREMENT_COHORT_GRAIN_REPAIRED_REAL_MULTI_EVIDENCE_CREATED`**, with
`REAL_MULTI_EVIDENCE_AGGREGATION_UNAVAILABLE_MISSING_RELIABILITY` beside it.
**Claims with more than one Evidence row: 0 → 2**, on real canonical data, with
zero network acquisitions.

**Two defects of one shape, both a docstring disagreeing with its code.** The
cohort key called currency and amount scope load-bearing and contained neither;
`_persist_evidence` claimed idempotency on `(workspace, claim, signal)` while the
query added `extraction_method`. The validation settled the first: `derive`
refuses unless currency and scope are single-valued, so the implementation was
wrong.

Extractor `procurement-value-contrast` 1.0.1 → 1.1.0. Minor, because adding a
field to a grouping key can only split groups — verified against the historical
division-90 Signal, which re-derived with every semantic field identical.

Evidence identity is now epistemic; interpreter version is provenance. A changed
assessment is reported as a conflict and nothing is written.

Counters: Signals 29 → 33, Claims 31 → 37, ClaimRevisions 32 → 38, Evidence
31 → 39. RawRecords, NormalizedRecords, ReliabilityAssessments, Opportunities,
independence groups and scope relations all unchanged.

New: `docs/data/procurement-grain-reproducibility-v1.json`,
`docs/data/second-pilot-regrain-run-v1.json`,
`docs/data/second-pilot-aggregation-v1.json`, and three scripts under
`infrastructure/scripts/`.

Report: `docs/architecture/mission-1.41-report.md`.

## 1.69 — 2026-09-03 (Sprint 1 / Mission 1.40)

**`SECOND_PILOT_REAL_MULTI_EVIDENCE_NOT_OBSERVED`.** CPV division 92,
"Recreational, cultural and sporting services", selected under a frozen ordinal
rule with every label verified one concept per fetch against the Publications
Office authority register. 177 notices acquired across two frozen windows, both
complete bounded queries.

**Three of four cohorts were refused for mixed currencies** and window A produced
no Signal at all, so the corpus still has 0 Claims with more than one Evidence
row. §37 forbids widening the window or switching category, and neither was done.

**The extractor's cohort key does not contain what its docstring says**: currency
and amount scope are named as load-bearing dimensions and are absent from the key,
so a currency-mixed division is refused whole rather than split. Not fixed here,
because changing a grouping key after seeing which data it rejected is the shape
§37 and §41 refuse.

**A duplicate Evidence row was created by this run and removed**: re-interpreting
the pre-existing division-90 Signal wrote a second row differing only by
interpreter version, briefly making the corpus report a false multi-record Claim.

Counters: RawRecords and NormalizedRecords 148 → 325, Signals 28 → 29, Claims
28 → 31, Evidence 28 → 31. Reliability assessments, Opportunities, independence
groups and scope relations all unchanged.

New: `docs/data/second-pilot-ted-category-selection-v1.json`,
`docs/data/second-pilot-acquisition-run-v1.json`,
`docs/data/second-pilot-pipeline-run-v1.json`,
`infrastructure/scripts/run_second_pilot_acquisition.py`,
`infrastructure/scripts/run_second_pilot_pipeline.py`.

Report: `docs/architecture/mission-1.40-report.md`.

## 1.68 — 2026-09-03 (Sprint 1 / Mission 1.39)

**`PROPOSITION_CONVERGENCE_CONTRACT_READY`.** Two genuinely distinct observations
can now support one Claim. Every live canonical counter is unchanged and the
calibration feasibility audit is byte-identical.

**ADR-035 introduces the distinction the Claim model did not make**: proposition
identity facts decide what is asserted, witness observation facts decide which
observation demonstrates it. A witness fact is not discarded — it stops being an
identity.

**OBSERVED convergence is legitimate and narrow.** An existential over a
publication passes the epistemic contract's own test, and the broader proposition
is entailed by the detailed one rather than a weakened copy, which is why it is a
new proposition kind and `notice_ids` stays identity on the old one.

**`max(members)` finally receives more than one member**, proved through the real
repository and the real aggregator against synthetic fixtures in a disposable
workspace: one Claim, two Evidence rows, one revision, idempotent replay.
Independence stays UNKNOWN and saturation still receives one group, which is
correct rather than a shortfall.

A test caught a vocabulary collision: `ObservationOverlap` was drafted with
`UNKNOWN`, which `EvidenceIndependenceState` already has. Renamed `UNESTABLISHED`.

New: `docs/architecture/adr/ADR-035-proposition-identity-and-witness-identity.md`,
`docs/data/proposition-convergence-contract-v1.md` and its generated artifact,
`packages/claim-model/python/sros_claim_model/convergence.py`,
`services/nlp/python/sros_nlp/interpreters/convergent_witness.py`,
`infrastructure/scripts/render_convergence_contract.py` (CI `--check`).

Report: `docs/architecture/mission-1.39-report.md`.

## 1.67 — 2026-09-03 (Sprint 1 / Mission 1.38)

**`MULTI_EVIDENCE_CLAIM_ARCHITECTURE_GAP`.** No second pilot selected, no
acquisition, every canonical counter unchanged, and the calibration feasibility
audit byte-identical before and after.

**Mission 1.37 found the symptom, this found the cause.** One Evidence per Claim
is not an accident of the corpus: every implemented interpretation is a
one-to-one restatement of one Signal. The persistence layer already supports N
Evidence on one Claim, and the aggregation framework is written for N; only the
production path cannot reach it.

**Convergence is one proposition fact away, and that fact is the measurement.**
All seven templates carry `source_id` plus the measurement identity plus the
period labels. Measured: 28 Claims, 28 distinct keys, closest pairs differ by
exactly one fact, and in twelve pairs it is `content_id` — Docker, Podman and
Kubernetes on the same day.

**Half the behaviour is correct and must not be repaired**: for an OBSERVED
claim, attribution is the claim, so deleting `source_id` is not the fix.

Six candidates evaluated. The two that pass taxonomy and governance fail on the
architecture; the two that pass the architecture fail on taxonomy; the best
domain diversity is blocked at the eligibility gate, where 22 of 29 sources sit.

New: `docs/data/second-pilot-selection-v1.json`.

Report: `docs/architecture/mission-1.38-report.md`.

## 1.66 — 2026-09-03 (Sprint 1 / Mission 1.37)

**`CALIBRATION_STRATEGY_READY_REFERENCE_DATA_MISSING`.** A preregistered
calibration methodology for the Evidence Aggregation framework, and no reference
data to run it on. 0 parameters fitted, 0 profiles calibrated, 0 model calls, 0
acquisitions, D-03 unchanged.

**Measured against the live database: every Claim has exactly one Evidence row.**
28 Claims, 28 Evidence rows, distinct evidence-count-per-claim `[1]`. The
aggregation layer has never aggregated, so saturation, independence collapse and
contradiction accumulation have no real-data exercise at all, and `min()` is
indistinguishable from returning the reliability value.

**The Mission 1.1 calibration plan proposes the wrong target**, and correcting it
is this mission's substantive finding. Its §5 calibration curve against outcome
resolution measures the state of the world, against a framework whose §1 says it
is not a truth estimator.

**A second gap restricts rather than blocks:** nothing anchors the absolute score
scale, so calibration targets the ordinal construct and absolute level is out of
scope until the framework supplies an anchor.

New: `docs/data/evidence-aggregation-calibration-strategy-v1.md` and its
machine-readable artifact, `docs/data/calibration-reference-dataset-schema-v1.json`
(empty by design), `docs/data/calibration-feasibility-audit-v1.json`,
`infrastructure/scripts/audit_calibration_feasibility.py`.

Report: `docs/architecture/mission-1.37-report.md`.

## 1.65 — 2026-09-03 (Sprint 1 / Mission 1.36.1 close-out)

**`DOCKER_RELIABILITY_PARTIALLY_REVIEWED`.** The operator typed the confirmation
the mission could not, so the Wikimedia assessment is recorded:
`e2419f13-c031-44d5-837c-c56a867baf34`, version 1, `HUMAN_REVIEW`, `thibchm`,
`0.65`, two document-backed basis rows.

**Two counters moved and fifteen did not.** ReliabilityAssessments 1 to 2, basis
rows 4 to 6. Six Wikimedia Evidence rows now resolve against that one assessment,
both Stack Exchange scopes stay `NO_APPLICABLE_ASSESSMENT`, TED is untouched at
version 1, and the negative checks went from three to six and still find no leak.

**`scoring.evidence.reliability` is still NULL on all 28 rows.** Six rows resolve
a number and none stores it, because reliability binds late (ADR-026 Decision 2).

**§15's diagnostic aggregation ran**, its precondition finally true: eight
single-record aggregations, `q = 0.650` on the six with `reliability` as the
limiting component, level still 1, the two refused scopes `UNAVAILABLE` with
`uncertainty_mass` 1.0, profile still `UNCALIBRATED`, nothing persisted. D-03
blocker 2 moves OPEN to PARTIAL; the other four do not move.

New: `docs/data/docker-diagnostic-aggregation-v1.json`,
`infrastructure/scripts/report_docker_diagnostic_aggregation.py`.

## 1.64 — 2026-09-03 (Sprint 1 / Mission 1.36.1)

**`OPERATOR_CONFIRMATION_REQUIRED`.** The operator reviewed all three reliability
scopes and decided differently about them: **NO** on both Stack Exchange scopes,
and **0.65 / `HUMAN_REVIEW` / `thibchm`** on the Wikimedia one. The assessment
that decision authorises is written and validated end to end, and **not
persisted** — the recording tool requires a confirmation typed by a person, and
§7 forbids bypassing the guard that enforces it. **0 assessments created, every
canonical counter unchanged.**

**A NO is not a number.** The refusal on scopes 1 and 2 is recorded as prose,
because a refusal recorded as data would be a value and the next reader would use
it as one. It does not mean `reliability = 0`, `0.5`, low reliability or an
unreliable source: it means **no human reliability judgement exists**, the
reliability stays `NULL`, and the Evidence stays `NON_SCORABLE`.

**Mission 1.36 shipped a real defect and this mission found it.** The packet's
`candidate_basis_rows` carried `basis_type` values that are not members of
`ReliabilityBasisType`, so the rows it prepared could not have recorded an
assessment — which is the one thing candidate basis rows are for. Repaired
against the TED precedent, with the narrative document list's field renamed
`document_kind`, and a test now asserts every row's type against the contract.

New: `docs/data/docker-reliability-operator-decisions-v1.md`,
`docs/data/docker-wikimedia-reliability-review-v1.json`,
`docs/data/docker-reliability-resolution-v1.json`,
`infrastructure/scripts/report_docker_reliability_resolution.py`.

Report: `docs/architecture/mission-1.36.1-report.md`.

## 1.63 — 2026-09-03 (Sprint 1 / Mission 1.36)

**`READY_FOR_OPERATOR_RELIABILITY_REVIEW`.** The reliability question is prepared
for the Docker Opportunity's Evidence, and software supplied no answer.

**Three distinct reliability scopes over the 8 rows, not two.** The two Stack
Exchange signal types share four of the five scope fields and persist different
`proposition_kind` values, so they are two reliability questions rather than one.
1 + 1 + 6 = 8, every row in exactly one scope.

**No reliability value appears anywhere** — no number, no range, no
recommendation, no adjective ranking a source. `reliability: null` means no
assessment exists, never 0.0 or 0.5, and the scale carries no threshold labels.

Wikimedia's pageview methodology was retrieved; Stack Exchange's is unreachable
because the site's robots policy blocks the crawler, so several questions a
reviewer needs — above all whether an accepted answer can later change —
are open, and the operator supplying the documents is the route Mission 1.18
used.

New: `docs/data/docker-evidence-reliability-review-packet-v1.md` and its
machine-readable packet with a blank operator worksheet, a packet builder that
has no field in which to put a value, and 38 tests whose load-bearing assertions
are negative.

**0 assessments created, all fourteen counters unchanged**,
`scoring.evidence.reliability` NULL on every row, profile still `UNCALIBRATED`,
four of five D-03 blockers open. Next: **stop and request the operator's
reliability decisions**.

Report: `docs/architecture/mission-1.36-report.md`.

## 1.62 — 2026-09-03 (Sprint 1 / Mission 1.35)

**`NO_AUTHORITATIVE_DOCKER_CATEGORY_RELATION_FOUND`.** The scope-relation
capability built in Mission 1.34 went looking for its first edge. Six
authoritative candidates, six rejections, **0 relations before and after**.

They fail in three distinct ways: sources that NAME Docker without classifying it
(its own documentation describes it functionally; the OCI defines specifications
and uses *container engine* as a term with no register behind it), a source that
classifies products but does not contain Docker (the CNCF Landscape lists Swarm,
Compose, Hub, a Wasm entry and the COMPANY - **not the container platform**), and
sources that classify what is *bought* rather than what a thing is (CPV, UNSPSC).

CPV is `CPV_NOT_SUITABLE_FOR_DIRECT_PRODUCT_RELATION` because a contracting
authority assigns a code to its own contract, so a CPV class contains
procurements and never products. UNSPSC returned HTTP 403 and is recorded
unresolved rather than guessed.

New: `docs/data/docker-commercial-scope-mapping-v1.md` and its machine-readable
record, plus 24 tests holding the documented refusal. The relation registry now
records why it is empty.

**0 model calls, 0 new canonical records**, all thirteen counters unchanged.
Next: **Reliability / Scoring Eligibility Foundation**, chosen explicitly over a
second pilot Opportunity.

Report: `docs/architecture/mission-1.35-report.md`.

## 1.61 — 2026-09-03 (Sprint 1 / Mission 1.34)

**`MULTI_SCOPE_ARCHITECTURE_READY_SCOPE_RELATIONS_UNPOPULATED`.** The engine can
now say what LEVEL of thing an Evidence row observes, separately from the subject
an Opportunity is about.

`SubjectScopeType` — `PRODUCT | CATEGORY | MARKET | GEOGRAPHY` — with
`ObservationScope`, a typed `ScopeRelation` model, three support roles
(`DIRECT_SUBJECT_EVIDENCE`, `BROADER_SCOPE_CONTEXT`, `GEOGRAPHIC_CONTEXT`), a
`ScopedDimension` triple that cannot be read without its scope, and a
fail-closed admission gate.

**The relation registry ships empty, and that is the outcome.** Mission 1.33
refused to assert which category contains Docker and §33 forbids inventing one,
so the capability holds zero edges and no Evidence row can currently be
contextual. Demonstrated on the real 28-row corpus: Docker resolves `PRODUCT`
(8 rows, direct), TED resolves `CATEGORY` on the publisher's own authority, and
offering TED to the Docker Opportunity is refused `NO_PERMITTED_RELATION`.

**No migration.** Scope is derived at packet-build time from identifiers already
held; persisting a derivation is what `source-registry-v1.md` §3 refuses.
Compatibility was proven by regenerating the preparation artifact: exactly one
field differed, the registry version.

New: `docs/data/observation-scope-rules-v1.json`,
`docs/data/scope-relation-registry-v1.json`,
`docs/data/opportunity-multiscope-sufficiency-design-v1.md` (design only, not
activated), and 65 tests. The canonical subject registry moved to
`canonical-subject-registry@1.1.0`.

**0 model calls, 0 network calls, 0 new canonical records**, all thirteen
counters verified unchanged, Opportunity revision 1 and its 7 links untouched.

Report: `docs/architecture/mission-1.34-report.md`.

## 1.60 — 2026-09-03 (Sprint 1 / Mission 1.33)

**`COMMERCIAL_SOURCE_GRAIN_MISMATCH`.** A desk review of all 29 registered
sources, asking which could produce an observation at the grain of
`subject:docker` that would support a commercial Opportunity dimension.

**The sources that can name Docker carry no commercial semantics; the sources
that carry commercial semantics cannot name Docker.** 5 identify Docker at grain,
7 reach it only as a mention, 17 not at all. 3 could support a missing commercial
dimension and all 3 are blocked — `github` and `product-hunt` by findings about
the PURPOSE of the use, which the local profile does not change, and `reddit` by
unretrievable terms plus a missing inference layer.

**The binding constraint is architectural.** `CanonicalSubject` has no scope
field and a packet holds one subject, so SROS models geographic scope on an
Opportunity and no subject scope at all — while `MARKET_ACTIVITY` and
`ECONOMIC_VALUE` already ask about *the bounded scope observed*. TED is
authorized, collected, normalized, extracted and carries three commercial
dimensions; its subject key is `ted-eu:CPV-division:90`.

New: `docs/data/commercial-dimension-source-feasibility-v1.md` and its
machine-readable matrix, plus 34 tests holding the three questions apart.

**0 acquisitions, 0 model calls, 0 new canonical records**, and all thirteen
counters verified unchanged against the live database. Recommendation:
`NO_CURRENT_SOURCE_CAN_CLOSE_DOCKER_COMMERCIAL_DIMENSION`, and a **Multi-Scope
Opportunity Evidence Architecture V1** mission before any acquisition.

Report: `docs/architecture/mission-1.33-report.md`.

## 1.59 — 2026-09-03 (Sprint 1 / Mission 1.32)

**`COMMERCIAL_EVIDENCE_CREATED_NO_OPPORTUNITY_DIMENSION`.** The held Docker
corpus was asked whether `has_accepted_answer` could support `SOLUTION_GAP` or
`SOLUTION_DISSATISFACTION`. It supports neither, and the measurement is real
anyway: **88 eligible questions, 34 with an accepted answer, 54 without** (38
answered but unaccepted, 16 with zero answers, 0 missing the flag).

The semantics were **frozen before any Signal existed**, in
`docs/data/answer-acceptance-semantics-v1.md`, and both dimensions were refused
there. `SOLUTION_GAP`'s own `never_means` forbids reading an absence of evidence
as evidence of absence; `SOLUTION_DISSATISFACTION` needs somebody evaluating
something, and an asker is not.

New: signal type `community_question_without_accepted_answer_volume` (migration
0031, reusing the ADR-034 family), extractor
`community-question-without-accepted-answer@1.0.0`, interpreter template seven
(`observed-signal-restatement@1.4.1`), and
`infrastructure/scripts/run_community_question_acceptance.py`.

Counters: Signals, Claims and Evidence 27 -> 28; ClaimRevisions 27 -> 29, because
the first wording implied a denominator and was corrected in place as revision 2.
**RawRecords and NormalizedRecords unchanged at 148** — nothing was acquired. The
Docker packet went 7 -> 8 rows with **counting dimensions unchanged at 2**, still
`HYPOTHESIS_FORMABLE`, still `AVAILABLE`, independence `UNKNOWN` for 8 of 8. 0
model calls, no Opportunity revision, problem-family still PARKED.

Report: `docs/architecture/mission-1.32-report.md`.

## 1.58 — 2026-09-03 (Sprint 1 / Mission 1.31.1)

Authorized by the Mission 1.31.1 brief §0-§22.

**OUTCOME: `FIRST_OPPORTUNITY_HYPOTHESIS_CREATED`. SROS holds its first
Opportunity.** One logical call, **0 retries**, 5 967 in / 2 722 out, **0.0392
USD** against a 0.25 ceiling. Decision `FORM_HYPOTHESIS`, every clause of the
frozen gate passed, and one Opportunity, one revision and **seven** Evidence
links were persisted -- all at `ELIGIBLE_CONTEXT`.

**EVERYTHING ELSE IS UNCHANGED.** RawRecords 148, NormalizedRecords 148, Signals,
Claims, ClaimRevisions and Evidence 27 each, ReliabilityAssessments 1, Embeddings
0, Scores 0, sources 29.

**MISSION 1.31 IS UNTOUCHED** and keeps `OPPORTUNITY_SYNTHESIS_OUTPUT_REJECTED`
under `audit@1.0.0` in its own artifact. This run wrote a new one. Neither
rewrites the other.

**THE PROMPT HASH IS BYTE-IDENTICAL.** `synthesis_prompt_hash()` still returns the
value Mission 1.31 recorded, so the question was re-asked and not re-tuned: the
packet, the evidence, the schema and the prompt are the same, and only the audit
differed.

**§1's FIVE REQUIRED CASES FOUND THAT `guard@1.1.0` HANDLED FOUR.** The fifth --
*competitors ARE NOT established by the evidence* -- is a denial whose marker
FOLLOWS its term, and 1.1.0 only cleared markers that preceded one. `@1.2.0` adds
that single grammatical form, cancelled by an intervening comma or contrastive
word, so *buyers would pay, which is not established* still fails. Order alone was
not enough; grammar was. Checking the cases also exposed an **off-by-one** in
`_phrase_position`, which returned the position of the character captured before
the word -- the one that stops `supermarket` matching `market` -- and had
misaligned the tail for every term not at the start of a sentence.

**THE TWO RUNS AGREE ON EVERY STRUCTURAL JUDGEMENT**, which is the strongest
available evidence that Mission 1.31's rejection was a guard defect and not a
model failure: same `UNKNOWN_NOT_SUPPORTED` actor, same twelve unsupported
dimensions, same seven citations, `commercial_claims_supported` empty in both.
This run's wording is arguably more careful -- *"at least momentary unserved need
at the point of asking"* bounds the reading to the instant of publication, and its
intervention field declines to name a class at all because *"the packet itself
does not support naming a product, feature, or service class"*.

**`market_scope` IS GLOBAL AND THAT IS NOT A MARKET CLAIM.** The column is NOT
NULL and the packet establishes no geography; Ontology V2 §4 defines GLOBAL as the
ABSENCE of a geographic restriction. The limitation is persisted on the revision
rather than left for a reader to infer.

**FOUR TED REVIEW TESTS WERE REPAIRED, on a precedent already written in their own
comments.** They asserted `research.opportunities == 0` as a proxy for *this
review created nothing*; that count is now legitimately non-zero on a machine that
has run the pipeline, exactly as RawRecords and NormalizedRecords became in
Missions 1.15.7 and 1.15.8. The replacement is stronger rather than looser: **no
Opportunity hypothesis cites TED Evidence**, on any machine
(`testing-strategy.md` §68).

**Next: targeted commercial evidence completion, not ranking.** There is one
Opportunity and nothing to rank it against, every supporting row is NON_SCORABLE,
and D-03 is untouched. The hypothesis names its own priority, and the narrowest
reachable dimension is SOLUTION_DISSATISFACTION over the accepted-answer field
already held and deliberately unread

## 1.57 — 2026-09-02 (Sprint 1 / Mission 1.31)

Authorized by the Mission 1.31 brief §0-§25.

**OUTCOME: `OPPORTUNITY_SYNTHESIS_OUTPUT_REJECTED`.** The first bounded
Opportunity synthesis ran against the real `docker` packet through the approved
route. One logical call, 0 retries, **0.0383 USD** against a 0.25 ceiling. The
model returned `FORM_HYPOTHESIS` with a careful, well-cited, bounded hypothesis,
and **the frozen persistence gate refused it on exactly one clause -- which is a
defect in the guard, not an over-reach by the model.** No Opportunity persisted;
every canonical counter unchanged.

**THE REJECTED SENTENCE IS THE ONE THAT OBEYED THE BRIEF.** The model wrote *"No
statement in the packet establishes ... whether anyone would pay, whether
competitors already serve this space ..."*, which is the enumeration of absences
§6 and §16 require. A token-based guard flagged `would pay` and `competitors`
because **it cannot see negation** -- `testing-strategy.md` §23 in a new place,
where a scan fires on the text that obeys the rule.

**THE VERDICT WAS KEPT AND THE GUARD FIXED FOR NEXT TIME.** §12 forbids weakening
a gate after seeing the answer, and this was identified as a defect BECAUSE it
rejected an output that looked sound -- exactly the reasoning that rule distrusts.
So the run keeps `audit@1.0.0`, nothing was persisted, and
`opportunity-claim-guard@1.1.0` reaches the next mission instead of rescuing this
one. The fix is scoped to one sentence, ignores markers appearing after the term,
and is tested against the exact rejected clause.

**TWO ATTEMPTS WERE ABANDONED BEFORE THAT, AND THE CAUSE WAS ALSO MINE.**
`max_output_tokens` was 1500 and the 17-field schema admits about 1800 tokens, so
the first call and its one permitted retry both came back missing five required
fields -- the model never finished an answer. **Bounding an output below what the
requested schema can serialise is a defect, not a discipline.** Raising a
transport bound and re-running is not the retry-shopping §10 forbids, because no
answer existed to reject; both wasted attempts are counted in the artifact.

**THE SYNTHESIS DID THE HARD PART WELL.** `target_actor_if_supported` came back
`UNKNOWN_NOT_SUPPORTED` rather than an invented persona; the intervention is a
CLASS and says so; the pageview evidence is restated as day-to-day FLUCTUATION
rather than growth, which is right because two of six rows are decreases;
`commercial_claims_supported` is EMPTY; all eleven mandatory unsupported
dimensions were reported plus `TREND_OR_CHANGE` unprompted; and the model
independently wrote that the question count is *a count of questions, not of
people* and *not evidence the questions share a single problem* -- reaching the
boundary Mission 1.27 parked without being told about it.

**EVERY OTHER GATE HELD.** Authorization resolved before serialization; the
transmitted payload was the nine-key Mission 1.29 allowlist and nothing else;
prompt regions stayed apart with each claim statement as `UntrustedText` labelled
by its ids; cited ids all belonged to the packet; every Evidence was cited with
its Claim; independence stayed UNKNOWN and reliability stayed NON_SCORABLE.

**Next: re-run the bounded synthesis under the corrected guard**, one call at
about 0.04 USD on an unchanged packet and prompt hash. It needs operator
authorisation because it re-asks a question this mission spent its allowance on.
Do not build ranking whatever it returns: every row is still NON_SCORABLE and
D-03 is untouched

## 1.56 — 2026-09-02 (Sprint 1 / Mission 1.30)

Authorized by the Mission 1.30 brief §0-§23.

**OUTCOME: `TARGETED_EVIDENCE_COMPLETION_SUCCESS`.** The `docker` packet is
**HYPOTHESIS_FORMABLE** and **AVAILABLE_FOR_EXTERNAL_SYNTHESIS**, on 7 Evidence
rows across two source families carrying two counting dimensions. Signals,
Claims, ClaimRevisions and Evidence 26 -> **27**; **RawRecords and
NormalizedRecords UNCHANGED at 148**; Opportunities, Embeddings and Scores still
0; **0 model calls, 0.00 USD**.

**THE MINIMUM NEEDED WAS ZERO.** §7 says collect the minimum and prefer fewer.
Mission 1.20 had already collected `tagged=docker` over 2024-03-01 to
2024-03-31, and that retrieval **provably did not truncate**: one page with
`page_size = 100` returned 89 records, and a short page means the result set was
exhausted. So a complete set already existed for one subject and nothing was
acquired.

**A TRUNCATED COUNT IS NOT MERELY IMPRECISE, IT IS ANTI-INFORMATIVE**, and that
is why Kubernetes and Podman were not reached. Capped at §7's 30 records, a
retrieval returning 30 would report OUR BOUND rather than the world -- and would
read as a LARGER number than a complete count of 88. The extractor therefore
REFUSES rather than qualifying, which is ADR-021's rule applied to a failure mode
that counting introduces and change never had.

**89 RETURNED, 88 COUNTED.** One record came back from a `tagged=docker` query
carrying no `docker` tag at all. What the query asked and what the site says are
different facts, and the site's own tag list is the one a claim about the site's
tag can rest on. It also settles Kubernetes: its two held questions arrived
through a Docker query and are a biased subset, not a count.

**ADR-034, A FIFTH QUANTITY FAMILY, AND THE NEAR MISS WAS THE DANGER.**
`CONTENT_REQUEST_VOLUME` would have fitted field for field. **A request is
something a READER makes of a server; a question is something a PERSON publishes
about being stuck.** Widening it would not have cost a FIELD its meaning, it
would have cost the FAMILY its meaning. `PROBLEM_VOLUME`, `USER_PAIN_VOLUME` and
`COMMUNITY_DEMAND` were available and all wrong: a family named for problems
would make the PARKED relation look answered by a count. The new record kind
supplies the temporal facts and NOT `EXACT_NUMERIC_VALUE`, because a question
carries no measured value.

**`PROBLEM_OR_NEED`, WITH `RECURRENCE_OR_FREQUENCY` REFUSED.** A published
question is a person saying they are stuck. Recurrence would require knowing the
questions concern the same problem, which is the relation Mission 1.27 parked, so
claiming it would recreate `SAME_PROBLEM_FAMILY` under another name.

**A CANONICAL SUBJECT REGISTRY MAY JOIN TWO VOCABULARIES; A CLASSIFIER MAY NOT.**
Packets were source-scoped by construction. The registry maps EXACT rendered keys
with a stated basis per entry, by equality and nothing else -- no distance, no
token overlap, no stem, no synonym table, no threshold -- and records what it
refuses: nothing unites Docker, Podman and Kubernetes, and `docker-compose` is
not folded into `docker`.

**NOTHING ELSE MOVED.** The sufficiency rule is unchanged at
`opportunity-sufficiency@1.0.0`, `TREND_OR_CHANGE` still does not count, the new
row is `ELIGIBLE_CONTEXT` with reliability NULL and `eligible_scoring` is still
0, and independence is `UNKNOWN` on all seven rows -- two source families is
diversity, not established independence. 33 new tests; six existing updated and
four made STRICTER, including two Mission 1.28 totals that now assert the count
agrees with the report's own row list.

**Next: Mission 1.31, First Bounded Opportunity Synthesis V1** -- recommended by
the NEXT-STEP RULE and not started

## 1.55 — 2026-09-02 (Sprint 1 / Mission 1.29)

Authorized by the Mission 1.29 brief §0-§18.

**OUTCOME: `OPPORTUNITY_SYNTHESIS_EGRESS_PARTIALLY_READY`.** Three of the four
source families that contribute canonical Evidence now have an
`external_model_transmission` decision; the fourth was assessed and could not be
recorded. **8 of 9 Opportunity packets are egress-authorized, 0 are formable, 0
model calls, 0.00 USD**, every canonical counter unchanged and authorizable
(source, profile) pairs 8 before and 8 after.

**THE DECISIONS.** `wikimedia-pageviews` **PERMITTED** -- the only unconditional
permission in this catalog, because CC0 1.0 waives all Copyright and Related
Rights including database rights BY NAME and leaves no act for a licence to
restrict. **No attribution condition was written**, because CC0 creates none and
Mission 1.19 established that inventing one leaves a reader unable to tell a duty
from a habit. `world-bank` and `gdelt` **PERMITTED_WITH_CONDITIONS**.

**TWO ACTS, ONE LIMIT.** CC BY 4.0 §2(a)(1) grants *"reproduce and Share"*, §1
defines Share as providing material *"to the public"*, and §3(a)(1) triggers
attribution only on Sharing. A contracted processor is not the public, so a
transmission is reproduction -- granted outright, with no boilerplate to paste
into a prompt. **The transmission allowlist is CC-BY-4.0 ONLY, tighter than
acquisition's**, because ODbL's *Publicly Use* is unanswered and an unanswered
question is not a permission.

**A GRANT'S SUBJECT BOUNDS IT.** GDELT permits *"unlimited and unrestricted use
... of any kind"* over *"all datasets released by the GDELT Project"* -- ngram
aggregates. **Third-party article text is not a GDELT-released dataset** and is a
prohibited representation. And GDELT's citation obligation attaches to *"any
use"*, so it is LIVE where CC BY's, which begins *"If You Share"*, is not.

**RECORDING A DECISION IS NOT FREE, AND THAT IS THE MISSION'S REAL FINDING.**
TED's `UNCLEAR` required appending a review version, and appending one **orphans
the operator's acceptance** of `ted-database-right-residual-exposure-accepted` --
a `HUMAN_CONFIRMATION` condition **no verifier may satisfy, by design**. Verified
against the real deployment rather than predicted: `build_authorization('ted-eu')`
refused and TED stopped being acquirable. §0 forbids letting a transmission
assessment rewrite acquisition eligibility, so **the append was withdrawn**.
NOT_ASSESSED and UNCLEAR both refuse, so nothing operational was lost; the
distinction lives in the governance document with **H-39** named and the operator
acceptance sentence written down -- and **writing it down is not recording it**.
**A source whose approval rests on a human decision cannot be cheaply amended**,
and that cost is invisible until a mission tries.

**UNRESOLVED IS NOT REFUSED.** `UNCLEAR` and `NOT_ADDRESSED` had no refusal code
and reported as a decision against. An operator can close an open question and
cannot argue with a decision.

**THE REPRESENTATION IS AN ALLOWLIST ENFORCED IN THE SERIALIZER**, not a promise:
nine permitted keys, named prohibited representations, personal-data markers at
every depth, refused rather than trimmed. **No raw source payload is transmitted
at all** -- only ids, procedure versions, subject keys, dimension bounds and Claim
statements this repository composed. One fail-open was found and fixed: the deep
scan tested `isinstance(dict)` while accepting any `Mapping`.

**THE MISSION 1.23 HAZARD FIRED AS DESIGNED.** The append stalled three
compliance pins and dropped authorizable pairs 8 -> 5; a performed re-check
asserting byte-identical `required_conditions` restored them to 8. A bespoke
before/after eligibility check had reported 0 regressions and MISSED it, because
it read the catalog and the pin lives in a separate file (`testing-strategy.md`
§66). Ten tests broke under the full append and
**withdrawing TED reverted seven of them cleanly**, leaving three real repairs and
none weakened -- two now name v1 explicitly and are stricter for it.

**Next: targeted evidence completion for subjects already in the packets**, not
broad source expansion. Wikimedia's three subjects need one genuinely different
dimension; TED's needs a second row and stays egress-blocked until H-39 closes.
Do not start scoring or ranking

## 1.54 — 2026-09-02 (Sprint 1 / Mission 1.28)

Authorized by the Mission 1.28 brief §0-§22.

**OUTCOME: `OPPORTUNITY_ENGINE_READY_BUT_CURRENT_EVIDENCE_INSUFFICIENT`.** The
architecture is built, tested and runs end to end over the real 26 canonical
Evidence rows. **26 rows inspected, 26 ELIGIBLE_CONTEXT, 0 ELIGIBLE_SCORING, 9
packets, 0 formable, 0 opportunity hypotheses, 0 model calls, 0.00 USD**, and
every canonical counter unchanged.

**§0 CORRECTION, REPORT TEXT ONLY.** Mission 1.27's §12 contradicted its §14 on
how often `shared_problem_if_any` came back empty. The persisted runs settle it:
**39 of 40 is correct**, and the §12 sentence named the right numbers with the
verb reversed -- 1 of 24 and 0 of 16 are the counts of rows where the field was
FILLED. No prediction, prompt version, cost or outcome touched.
`EXPLORATORY_V2_NOT_PROMISING` and `PARK_PROBLEM_FAMILY_CLASSIFIER` stand.

**WHAT ALREADY EXISTED, AND IT WAS MORE THAN NOTHING.** `research.opportunities`
has been a real RLS-protected table since Mission 0.1 with identity, scope and a
repository, and `research.claims.opportunity_id` already points at it. What was
missing was everything epistemic: status, procedure, evidence links, dimensions,
limitations, revisions. So the table was EXTENDED, never replaced -- a second
table would be a second place an opportunity can live, and one outside
`research.opportunities` escapes the RLS policy and every rule written about it.

**THE FAILURE IS SYMMETRIC, AND THAT IS THE FINDING.** The one packet carrying
commercial dimensions -- TED, CPV division 90 -- holds **one row**. The three
packets holding **six rows** each -- Wikimedia's Docker, Podman and Kubernetes --
carry **one counting dimension**. SROS's evidence is deep where it is narrow and
broad where it is shallow, and **nine of fourteen dimensions are answered by
nothing at all**, including every dimension that would make an opportunity
commercially interesting.

**THE SECOND BLOCKER IS INDEPENDENT OF THE FIRST.** All nine packets are
`UNAVAILABLE_FOR_EXTERNAL_SYNTHESIS`, and not because of the evidence:
`external_model_transmission` is **NOT_ASSESSED** for every source that HAS
Evidence and PERMITTED only for `stack-exchange`, which has none. **The one source
cleared to leave this deployment is the one source with nothing to send.** No
packet could have reached a model whatever the evidence looked like, so the §17
ceiling of 1.00 USD was never approached.

**THREE SIGNAL TYPES MAP TO NO DIMENSION, ON PURPOSE.** `numeric_period_change`
because what a period change bears on depends on WHICH indicator moved and no
reviewed indicator map exists; both GDELT lexical types because a term count
measures what media organisations PUBLISHED -- producer behaviour, not audience
behaviour -- so it is not even `AUDIENCE_OR_USAGE`. Adding a dimension so a source
had somewhere to land would be a taxonomy fitted to a sample.

**`TREND_OR_CHANGE` CANNOT SATISFY A DIVERSITY REQUIREMENT.** A Signal in this
repository IS a derivation over two or more observations, so every Evidence row
carries change by construction and a universal dimension separates nothing. The
qualifier was chosen with the corpus visible, is reported under both readings,
and **decides a label rather than the outcome**: under the literal reading the
three Wikimedia packets would be formable and all three would still be blocked at
the egress gate.

**DOCKER, PODMAN AND KUBERNETES STAY THREE PACKETS.** Merging them would be a
`SAME_PROBLEM_FAMILY`-shaped judgement reached by hand instead of by the
classifier Mission 1.27 parked. **Doing it deterministically would not make it
deterministic; it would make it unargued.**

**Migration 0029 is forward-only and non-destructive**, and its point is a CHECK
constraint: three hypothesis-grade states and no `VALIDATED_OPPORTUNITY`,
`PROVEN_MARKET`, `WINNING_IDEA`, `PRODUCT_MARKET_FIT` or
`HIGH_CONFIDENCE_BUSINESS`. **No score, rank, weight or leaderboard exists** in
the package or the schema, asserted over the AST. 72 new tests; two existing
schema tests failed on the new tenant tables and were REPAIRED rather than
relaxed, because a widened tenancy assertion ships the next missing RLS policy
green.

**Next: assess `external_model_transmission` for the four sources that have
Evidence.** It is a reading-and-deciding mission of the shape Mission 1.23
already ran, and until it happens no packet from this corpus can reach a model
however good the evidence gets. Do not start ranking

## 1.53 — 2026-09-02 (Sprint 1 / Mission 1.27)

Authorized by the Mission 1.27 brief §0-§16.

**OUTCOME: `EXPLORATORY_V2_NOT_PROMISING`. Recommendation:
`PARK_PROBLEM_FAMILY_CLASSIFIER`.** 88 logical evaluations, **1.53 USD**, 0
retries, every canonical counter unchanged, and no Signal, Claim, Evidence,
ReliabilityAssessment, Opportunity or Score created. Production problem-family
inference remains **NOT_AUTHORISED**.

**WHAT V1 ACTUALLY DID, from its own outputs.** 17 of 20 decisions DIFFERENT, 15
of them under one reason code, and goal fields filled to the 240-character cap
with frameworks and ports. On two pairs a human later called SAME, its rationale
*states the shared abstraction and then rejects it*. V1 was not failing to see
it. Everything beyond that is hypothesis and is labelled as such.

**THREE VARIANTS, A FROZEN RULE, ONE SELECTION.** Goal and blocker separated with
the goal capped at 120 characters; then a required shared-abstraction attempt;
then a permissive reminder. On DEVELOPMENT: V2-A and V2-C each found 1 of 2
provisional positives with 0 false, V2-B found 0 and was ineligible. The rule
broke the tie on simplicity. **Adding scaffolding made the classifier MORE
conservative, not less.**

**THE HOLDOUT SAID NO.** V2-A frozen with a prompt hash, run once: 0 provisional
true SAME against 4 references, where the criterion frozen beforehand required 2.

**THE MOST INFORMATIVE ARTIFACT WAS AN EMPTY FIELD.** V2 required the model to
name a problem abstraction covering both questions before deciding.
`shared_problem_if_any` came back empty on **39 of 40** evaluations. The model is
not rejecting candidate abstractions; it is not generating them. That is not a
prompt needing another turn of tuning.

**Three rules this mission added to the repository.** A selection rule must
defeat BOTH collapses -- constant-DIFFERENT and constant-SAME -- so the frozen
rule demands a true positive and caps the SAME share. A cost ceiling you might
exceed is bounded rather than argued away: output was capped at 1200 tokens to
make 3.00 USD a real bound instead of a nominal one. And **a split disjoint by
PAIR is not disjoint by OBSERVATION**: the brief's own suggested prompt
illustration was the exact abstraction of a holdout pair, and the development
pair that would have replaced it shares an observation with another holdout pair.
Both were refused and a test asserts no prompt names a corpus question id.

**Nothing historical was rewritten.** Mission 1.25 remains
`MODEL_EVALUATION_FAILED`, Mission 1.26 remains `REFERENCE_SET_INSUFFICIENT`, and
the genuine `HUMAN_OPERATOR` holdout remains what it is.

**Next: the Opportunity Engine over evidence paths already valid.** SROS holds 26
canonical Evidence rows from other source families; this relation is parked, not
the system

## 1.52 — 2026-09-02 (Sprint 1 / Mission 1.26 close)

The reference batch was labelled. **Outcome: `REFERENCE_SET_INSUFFICIENT`**, with
**zero model calls** and every canonical counter unchanged.

**THE LABELS ARE NOT HUMAN.** All 40 are `AI_ASSISTED_PROVISIONAL`, reviewer
GPT-5.6 Sol. The operator chose to proceed with them rather than spend another
mission hand-labelling -- recorded as a document-level `operator_decision`,
because the decision concerns a whole file and a per-label flag would need a
migration for nothing and would eventually be read as per-label approval. They
must never be described as HUMAN_OPERATOR, human ground truth, expert labels or
independently human-reviewed labels, and **a loader asked for HUMAN_OPERATOR
refuses them**.

**TWO RESULTS, REPORTED APART.** Composition: development holds **2**
`SAME_FAMILY` against a preregistered 4 and FAILS; holdout holds 4 and PASSES.
Epistemic: the human reference requirement is **NOT_ESTABLISHED**, independent of
the arithmetic. They fail for unrelated reasons and a single verdict would let
one hide the other.

**NOTHING WAS MOVED.** No pair changed split, no label was revised, no threshold
lowered, no re-sampling with different quotas. The whole value of a preregistered
gate is that it is allowed to fail, and this is the second consecutive mission
where holding a rule cost the project its result.

**WHAT THE FAILURE IS NOT.** Not evidence that the relation is invalid, that a V2
cannot work, that Stack Exchange cannot contribute recurring-problem evidence, or
that families are rare. The sample is enriched and estimates no prevalence. It
means only that under the frozen sampling and these provisional labels, the
development split lacks positives for the preregistered requirement.

**MISSION 1.25's HUMAN HOLDOUT IS NOT MERGED IN** to satisfy the threshold. Its
10 pairs, 2 `HUMAN_OPERATOR` positives, 0 true SAME predictions and
`MODEL_EVALUATION_FAILED` remain the strongest evidence about V1, separately
queryable.

**What the mission did deliver** is the infrastructure: blind batch creation,
deterministic stratified sampling, a split frozen before labels, structural
holdout isolation across separate files, and provenance that demonstrably
refuses to hand human-labelled data to a caller who has none. The provisional set
is usable for EXPLORATORY development; **production problem-family inference
remains NOT_AUTHORISED**, and a backlog item blocks the word *validated* until
genuinely human labels exist

## 1.51 — 2026-09-02 (Sprint 1 / Mission 1.26)

Authorized by the Mission 1.26 brief §0-§14. **A DATASET mission: no model call,
no classifier, no prompt, no evaluation.** Every canonical research counter is
unchanged and no Signal, Claim, Evidence or Opportunity was created.

**MISSION 1.25 IS PRESERVED EXACTLY.** `MODEL_EVALUATION_FAILED` stands in both
its scorings and is not reinterpreted. Its development split remains
`AI_ASSISTED_PROVISIONAL`, its human holdout stays in its own file, and its full
20-pair set stays MIXED provenance. Nothing in this mission reads, merges or
supersedes it: it remains separately queryable as `problem-family-evaluation-v1`.

**WHY A DATASET MISSION AT ALL.** Ten human-scored pairs holding two positives
were enough to reject a trivial classifier and are not enough to build or
credibly evaluate a successor. And when the operator reviewed those ten, five
labels changed and on three the human moved TOWARD the classifier -- so the
earlier reading that V1 was far too conservative was half an artifact of an
AI-assisted reference. **A conclusion drawn about a classifier from a provisional
reference is partly a conclusion about the reference.**

**40 NEW PAIRS, NONE SHARED WITH MISSION 1.25**, drawn from the 711 available
under the frozen eligibility rule by deterministic stratified sampling across
five feature bands, split **24 development / 16 holdout** before any label
existed. `problem-family-human-reference-v1`,
`problem-family-human-reference-sampling@1.0.0`.

**NO MODEL OUTPUT ENTERED THE SELECTION.** Not a prediction, a confidence, an
explanation, or the fact that a pair was ever predicted. A dataset selected by an
earlier classifier's errors can only ever measure that classifier, so the sampler
imports no gateway and no run artifact -- asserted by parsing its code with
docstrings excluded, since the module says *not a prediction* precisely because
it reads none.

**THE SAMPLE IS ENRICHED AND SAYS NOTHING ABOUT PREVALENCE.** Bands are drawn at
deliberately unequal rates: the low-similarity band holds 275 available pairs and
contributes 8, the wrapper band holds 2 and contributes both. The warning rides
on the dataset object.

**HOLDOUT ISOLATION IS STRUCTURAL.** The splits' labels will live in separate
files, and the development loader cannot reach a holdout label because it never
opens that file. Provenance is mandatory on load with no default, and
`HUMAN_OPERATOR` establishes human ground truth without being called expert
review -- the system does not establish that fact.

**Awaiting the operator's 40 labels.** The composition gates -- 12 non-UNCERTAIN,
4 SAME and 4 DIFFERENT in the holdout; 16, 4 and 4 in development -- are declared
now and are dataset gates, never classifier success criteria

## 1.50 — 2026-09-02 (Sprint 1 / Mission 1.25, human holdout re-scoring)

Authorized by the Mission 1.25 continuation. **No model call, and nothing frozen
touched**: rubric, prompt, candidate set, split, predictions and acceptance
criterion are unchanged, and the provisional scoring is preserved beside the new
result rather than replaced.

**THE CRITERION STILL FAILS, AND NOW AGAINST HUMAN GROUND TRUTH.** The scored
holdout meets every precondition -- 10 labelled pairs, 2 human `SAME_FAMILY`, 0
false positives -- and the model produced **0** true `SAME_PROBLEM_FAMILY`.
`MODEL_EVALUATION_FAILED` stands. **Zero false positives is not a pass**: it is
what a classifier hard-coded to answer DIFFERENT scores, which is why the
criterion asks a second question.

**BUT THE REFERENCE WAS HALF THE STORY, AND THAT IS THE FINDING.** Five of ten
labels changed under human review, and **on three the operator moved TOWARD the
model**: the provisional reference had called two pairs a family the operator
does not, and one pair decidable that the operator finds undecidable -- and the
classifier had already answered DIFFERENT, DIFFERENT and ABSTAIN on exactly
those. Missed positives fall from 4 to 2 and agreement rises from 5/10 to 6/10.

So Mission 1.25's reading that the classifier is *strictly more conservative than
the reference* was half an artifact of an AI-assisted reference. **A conclusion
drawn about a classifier from a provisional reference is partly a conclusion
about the reference**, which generalises past this mission.

**The one-directional pattern survives at half the size**: two human-confirmed
families were still missed, so the classifier cannot yet demonstrate it can find
one.

**PROVENANCE IS MIXED AND STAYS SO.** The scored holdout has human ground truth;
the development split remains `AI_ASSISTED_PROVISIONAL`. The full 20-pair set
must never be reported as fully human. `HUMAN_OPERATOR` was added as a reference
origin -- a person, so it establishes ground truth, and deliberately not filed as
expert or non-expert because neither is ours to assert on their behalf

## 1.49 — 2026-09-02 (Sprint 1 / Mission 1.25)

Authorized by the Mission 1.25 brief §0-§15.

**OUTCOME: `MODEL_EVALUATION_FAILED` on a frozen criterion, and the failure is
worth more than Mission 1.24's pass.** 20 pairs through the Gateway on the
approved route, **0.38 USD**, and every count unchanged at 148/148 records and
26/26/26/26 Signals, Claims, Revisions and Evidence. Catalog still 29 sources.
No production inference, no Signal, no INFERRED Claim, no Evidence.

**A SECOND RELATION, NOT A LOOSER FIRST ONE.** `SAME_PROBLEM_FAMILY` asks whether
two observations express substantially the same user problem or blocked goal, at
a level where one intervention could help both -- even where the causes and fixes
differ. The exact relation stays intact, unweakened and not redefined. The two
are held apart in code by `relations.py`, with the forbidden implications kept as
data a test checks rather than prose a reviewer must remember.

**THE RELATION CHANGED RATHER THAN A THRESHOLD.** Mission 1.24 found its question
hard to label for a structural reason: *would the fix transfer?* requires knowing
the fix. Loosening it would have kept that requirement while answering more
permissively.

**THE CRITERION WAS BUILT SO A CONSTANT CLASSIFIER CANNOT PASS**, which is what
Mission 1.24 lacked. `min_true_same` demands a demonstrated positive in the
scored split; tests score a constant-DIFFERENT and a constant-ABSTAIN classifier
and watch both fail. **Then it caught the real run**: the scored holdout held 4
`SAME_FAMILY` references and the model found **zero**, saying SAME once in twenty
overall -- on the rubric's own quoted example, which is in-sample by construction.

**EVERY DISAGREEMENT IS ONE-DIRECTIONAL.** Eight missed positives, zero asserted
families the reference denied. Either the rubric is too strict or the reference
too generous, and this evaluation cannot separate them -- the rubric and its
reference disagree about the rubric's own borderline example, with the model
siding with the rubric. **A question for a person, not for a rerun.**

**THE RUBRIC WAS NOT WIDENED AFTER SEEING THE RESULTS**, and the criterion was
not altered. Mission 1.24 kept a rule in the direction that flattered the
project; this keeps one in the direction that cost it.

**THE REFERENCE IS `AI_ASSISTED_PROVISIONAL`**, written blind and never sent to
the classifier, so what was measured is agreement between two assistants.
`human_ground_truth` stays NOT_ESTABLISHED, carried through to every evaluation
result rather than asserted in prose.

**Candidate generation was inspected, not assumed.** The existing generator is
not too narrow -- 731 of 3 916 pairs, 84 of 89 observations reached -- but its
ORDERING was built for the other relation. The qualifying predicate is imported
unchanged with a test pinning it; only the ordering is versioned, with a shared
diagnostic at weight ZERO and tags weighted by the rarest shared one.

**One structured response in twenty was malformed** -- a key emitted as the
literal `"parameter name"` -- and the Gateway refused rather than guessing, which
is correct and unchanged. The runner retries once against the same route and
counts it; that is not the cross-provider fallback ADR-006 forbids

## 1.48 — 2026-09-02 (Sprint 1 / Mission 1.25 §0-§1 corrections)

Authorized by the Mission 1.25 brief §0-§1. Documentation corrections made before
the mission proper begins. **No evaluation history was rewritten**: every label,
prediction, cost and outcome from Mission 1.24 is unchanged.

**THE REFERENCE LABELS WERE NOT HUMAN, AND THE REPOSITORY SAID THEY WERE.**
Mission 1.24's 40 labels were supplied `AI_ASSISTED_PROVISIONAL` by GPT-5.6 Sol,
not by an independent human domain expert. The claim was embedded in a filename
(`problem-equivalence-human-labels-v1.json`), a report section heading (HUMAN
EVALUATION), two type names (`HumanLabel`, `HumanDecision`) and a `reviewer`
field naming a person who did not make the judgements.

`ReferenceOrigin` is now required on every label and never defaulted, and
`human_ground_truth_established` is derived from it -- true only when EVERY label
came from a human, because a mixed set reported as `True` would be read as
unmixed. The origin is recorded on the RESULT as well as on the labels, since a
result is what gets quoted. **`human_ground_truth = NOT_ESTABLISHED`** for that
set, and the two Mission 1.24 disagreements are **not** human inter-rater
disagreement.

**What the reference set still is**: written blind, before any model call, never
sent to the classifier. That makes it valid for scoring, and what it measured is
**agreement between two assistants** rather than accuracy. Mission 1.24 remains
EVALUATION_INSUFFICIENT for the reason this correction does not touch -- the
holdout held no SAME label at all.

**AND SROS DOES HAVE EVIDENCE.** Mission 1.24 concluded SROS was not ready for
cross-source convergence *because this mission produced no evidence*, which does
not follow: **26 canonical Evidence rows** exist from other source families. The
precise gap is **no validated recurring-problem semantic evidence from Stack
Exchange**, bounded twice over -- to EXACT actionable problem equivalence, and to
one candidate set. Nothing there establishes that Stack Exchange cannot
contribute recurring problem-FAMILY evidence, a looser relation nobody has
evaluated

## 1.47 — 2026-09-02 (Sprint 1 / Mission 1.24)

Authorized by the Mission 1.24 brief §0-§35.

**OUTCOME B: EVALUATION_INSUFFICIENT_FOR_PRODUCTION_EQUIVALENCE.** The first
model-mediated inference this repository has ever run, and it produced **no
epistemic row at all**. 40 real labelled pairs through the Gateway on the
approved route, **0.61 USD**, and every count unchanged at 148/148 records and
26/26/26/26 Signals, Claims, Revisions and Evidence. Catalog still 29 sources.

**ZERO FALSE SAME, AND THE NUMBER IS WORTH ALMOST NOTHING.** The classifier
produced **zero SAME of any kind** across 40 pairs, and the holdout contained
**no SAME label to test against**. A classifier hard-coded to answer DIFFERENT
records exactly the same score. Precision on SAME is undefined -- there were no
predictions -- and recall is 0/1: the single positive in the whole reference set
was missed.

**THE PREDECLARED CRITERION WAS WRONG, AND ONLY DATA COULD SHOW IT.** V1 required
a positive *anywhere in the reference set*, and the only one fell in DEVELOPMENT
while the HOLDOUT held none. V2 requires it *in the split being scored* and
returns EVALUATION_INSUFFICIENT on the identical run and data. **V1 is kept and
Mission 1.24 stays scored under it**: a rule rewritten after seeing the result was
never binding, and the discipline matters more in the direction that would have
made the outcome look better.

**A STRUCTURAL GUARD DECIDED THE ARCHITECTURE.** `validate_signals.py` forbids a
Gateway import anywhere under `sros_nlp` and requires every module there to be
classified, so a model-calling component cannot live in the signal layer. The
guard was left untouched and `packages/semantic-equivalence` carries the work --
depending on contracts and the Gateway and on nothing else, in particular not on
the source registry, because a classifier able to read it could decide its own
authorization.

**AUTHORIZATION IS RESOLVED BEFORE ANY SOURCE TEXT IS SERIALISED**, not before
the socket. A refused pair produces no prompt containing question text, asserted
with a gateway double that raises if it is reached. Question text is
`UntrustedText` and can occupy no other region; the classifier gets no tools, no
browsing and no execution. **No confidence number is requested from the model at
all**: a self-reported certainty is not a probability, and the only safe handling
is to mark it uncalibrated and never do arithmetic on it, at which point asking
for it buys nothing.

**THE THREE MISSION 1.20 HARD NEGATIVES WERE CLASSIFIED CORRECTLY AND PROVE
NOTHING.** The rubric quotes one by id and describes the pattern the other two
share, so they are in-sample by construction. All three are pinned to
development, each with its reason recorded, because counting them as holdout
successes would have inflated the result.

**TWO DISAGREEMENTS RECORDED RATHER THAN TUNED AWAY.** The missed positive is a
Next.js build-time env var and a Compose build-stage env var: the same class of
misconfiguration under two different components, and both readings survive the
rubric. The rubric was NOT revised to capture it -- one example is n=1, the
revision would loosen toward more SAMEs, and no holdout positive exists against
which to measure the false-positive cost. Separately, the reviewer answered
UNCERTAIN on the rubric's own borderline worked example, where the rubric states
DIFFERENT: the rubric's author and its reviewer read a boundary example
differently, which is a defect in the example.

**No production inference, no model-derived Signal, no INFERRED Claim, no
Evidence, no Opportunity.** The blocker is a reference set with real positives in
the scored split, and this 89-question corpus yielded one defensible SAME in 40
candidate pairs -- a finding about the corpus rather than about the classifier.
No synthetic positive may substitute: a constructed pair can test a parser and
can never establish semantic accuracy against real data

## 1.46 — 2026-09-02 (Sprint 1 / Mission 1.23)

Authorized by the Mission 1.23 brief §0-§40.

**OUTCOME B: READY_FOR_OPERATOR_CONFIGURATION.** The governance question is
answered, the runtime gate is built and exercised, and the boundary is closed on
exactly one remaining condition. **No model was called, no source content left
this machine, 0 model calls, 0 tokens, 0 cost**, and every count is unchanged at
148/148 records and 26/26/26/26 Signals, Claims, Revisions and Evidence. The
catalog stays at 29 sources.

**THREE QUESTIONS THAT WERE ONE OR NONE** (ADR-033). `model_processing` asks may
a model READ this material -- Stack Exchange had answered it. The new
`external_model_transmission` asks may the material LEAVE this deployment so a
THIRD PARTY's model can read it. A new provider policy asks what that processor
DOES with what it receives. Different exposure, different counterparty, different
instrument. **Reinterpreting the first to mean the second would have granted
twenty-nine sources a permission nobody assessed**, so it was not touched.

**THE PROFILE GAINED THE WORD IT WAS MISSING.** `external_model_egress` closes
the gap Mission 1.22 named: `model_inference` said the ACTIVITY was in scope,
`deployment: LOCAL` said where the SYSTEM runs, and nothing said where inference
RUNS. Local is `PERMITTED_TO_APPROVED_PROVIDERS`; commercial is `NOT_ASSESSED`
**written out rather than inherited**, because whether a public multi-tenant
service may send third-party licensed content to a processor is a materially
harder question and a mission that answered it in passing would answer it for a
product nobody has built.

**NOT_ASSESSED IS A STATE, NOT A DEFAULT THAT DECIDES.** Migration 0027 adds both
columns nullable with no default and writes **no existing row** -- a mass UPDATE
would have invented sixty-four answers. Migration 0028 then writes only the two
decisions actually made, as a second migration because 0027 is applied and an
applied migration is immutable.

**DELIBERATELY NOT ONE OF RULE 8'S SIX.** The activity gates ONE operation, so
World Bank's deterministic collector never becomes ineligible because nobody
assessed model egress for World Bank. Asserted over **every** registered source
rather than assumed: no acquisition refusal mentions the activity or the word
*egress*.

**A PROVIDER IS APPROVED ON ITS OWN CONTRACT TEXT, AND THE ROUTE IS WHAT IS
ASSESSED.** One route is APPROVED on commercial terms committing that the
provider may not train models on customer content, with documented bounded
retention. One is NOT_APPROVED because its **unpaid** route states that submitted
content is used to develop machine learning technologies, that human reviewers may
read input and output, and that confidential information should not be submitted.
The same vendor's paid route is a different assessment nobody has made. **No
source review names a vendor** -- the condition states the PROPERTY a provider
must have, because naming a company would put provider governance inside the
source registry.

**APPENDING A REVIEW VERSION IS NOT FREE, AND THAT WAS FOUND THE HARD WAY.**
Stack Exchange local review v2 broke deterministic acquisition for the source: a
compliance configuration is pinned to a review version, on the stated ground that
a re-review can change what a condition means. **The guard is right and the repair
was to perform the re-check rather than silence it** -- v2's `required_conditions`
are byte-identical to v1's, asserted in code before the version was bumped and
pinned by a test, so a future review that DOES alter a required condition cannot
be waved through by editing a number.

**THE BOUNDARY IS CLOSED, BY NAME.** Live: source `PERMITTED_WITH_CONDITIONS`,
profile `PERMITTED_TO_APPROVED_PROVIDERS`, provider `APPROVED`, configured **no**
-> `PROVIDER_NOT_CONFIGURED`. No credential was fabricated, committed, or pasted
into a tracked file. **Mission 1.22's evaluation may RESUME after operator
configuration** -- and for the first time in this sequence the blocker is neither
the data nor the world nor a missing word, but a configuration step an operator
can clear.

**One older violation disclosed rather than left in a transcript**: Mission 1.19
edited an applied migration and committed it, which the 0026 checksum caught when
0027 would not apply. Repaired in the local ledger row only, verified from a fresh
connection, with no schema object altered and no migration file edited to fix it

## 1.45 — 2026-09-02 (Sprint 1 / Mission 1.22)

Authorized by the Mission 1.22 brief §0-§51.

**OUTCOME A: THE MODEL ROUTE IS NOT AUTHORISED, AND SEPARATELY NOT CONFIGURED.**
No model was called, no question text left this machine, no component was built.
0 model calls, 0 tokens, 0 cost, and every count unchanged at 148/148 records and
26/26/26/26 Signals, Claims, Revisions and Evidence.

**THE GOVERNANCE GATE, AND THE STRUCTURAL FINDING UNDERNEATH IT.** The Stack
Exchange review permits model INFERENCE -- *"Reading and classifying licensed
text is use within the licence's own grant to reproduce and to produce Adapted
Material"* -- and is **silent on TRANSMISSION** of that text to an external
provider. Those are different acts with different exposure. **The profile is
silent too, and has no word for the question**: `model_inference: true` says the
ACTIVITY is in scope and `deployment: LOCAL` says where the SYSTEM runs, while
nothing says where inference RUNS. No occurrence of *provider*, *third party*,
*transmit* or *egress* appears in the profile, in any condition on the review, or
in any document under `docs/` -- each absence searched for rather than assumed,
and each asserted by a test. **So `model_processing` is one field answering a
question that turns out to be two**, which is the same shape Mission 1.15.4 found
when every review had assessed a use case the model never recorded.

**THE SECOND GATE IS INDEPENDENT.** Every inference tier is `null`, every
credential is empty, and the only implemented providers are `anthropic` and
`gemini`, both external, plus test doubles. **There is no local inference
provider**: `local` appears once, as the EMBEDDING tier, and embeddings are
forbidden. §6's instruction to prefer a local route has no candidate to prefer.
Configuring a provider would not answer the governance question, and answering it
would not configure a provider.

**A DESIGN, NOT A COMPONENT.** `semantic-problem-equivalence-v1.md` records the
architecture -- bounded deterministic candidate generation that is never
evidence, a versioned rubric with mandatory ABSTAIN, untrusted question text
structurally separated from instructions, a classifier with no tools, uncalibrated
confidence semantics, pairwise-only Signals, provenance outliving the current
configuration -- and nothing was built, because building half a machine whose
other half is unauthorised is the unused abstraction this repository refuses
elsewhere. Mission 1.20's three Docker hard negatives are carried into the rubric
section so they are not rediscovered.

**§47's evaluation report was deliberately NOT created.** A rubric section, an
empty confusion matrix and "not evaluated" in every row would look like an
evaluation that returned nothing, when none was performed. No operator labelling
batch was requested either: asking a person to label pairs for a classifier that
cannot run spends attention on a step that cannot complete.

**Two 1.21 wordings corrected first.** Its pre-registration claim was too absolute
-- two metadata-only probes had already occurred -- and its robots finding is now
stated as an SROS POLICY DECISION rather than a legal conclusion: no sufficient
positive access basis exists under this repository's rules and the directive
disallows the route, and **neither amounts to a claim that robots.txt makes REST
access unlawful**. No acquisition became authorised by either correction.

**THE BLOCKER MOVED FROM THE WORLD TO THIS DEPLOYMENT.** 1.18 and 1.20 found the
DATA could not support deterministic identity; 1.21 found the SOURCES publishing
identity could not be reached; 1.22 finds that **the model route has not been
assessed and the profile cannot express the question**. The first two were
findings about the world; this one is about SROS, and is therefore the one this
project can resolve. Recommended next: a governance mission that asks where
inference may happen and gives the profile a field for the answer

## 1.44 — 2026-09-02 (Sprint 1 / Mission 1.21)

Authorized by the Mission 1.21 brief §0-§38.

**EXPLICIT ISSUE IDENTITY ROUTE = BLOCKED BY SOURCE GOVERNANCE.** 0 acquisitions,
0 records, 0 Signals, 0 Claims, 0 Evidence, and **the catalog is unchanged at 29
sources** -- the whole output is one Authoritative document and the tests that
pin it, which is the right shape for a mission whose product is a governance
finding.

**THE STRUCTURE EXISTS AND THE ACCESS DOES NOT.** Three public trackers document
a publisher-declared canonical duplicate relation as issue state -- Bugzilla's
`dupe_of` (*"The bug ID of the bug that this bug is a duplicate of"*), Launchpad's
`duplicate_of_link` plus `duplicates_collection_link`, and Debian's merges. So
Mission 1.20's proposed next route is real. **Every candidate publishing a usable
data licence also publishes a robots directive disallowing the API path, and the
only deployment whose directive permits it -- bugzilla.kernel.org -- publishes no
data licence at all.**

**THE DOCUMENT FOUNDATION BUGZILLA WON THE DATA QUESTION OUTRIGHT AND LOST THE
ACCESS ONE.** Its front page releases all contributions under **CC BY-SA 4.0** --
a licence on the TRACKER rather than on the tracker software, and TDF states them
per property (website 3.0, wiki 3.0 Unported, Bugzilla 4.0), so nobody copied a
footer. Bugzilla REST honours `include_fields`: a probe returned exactly six
fields, no reporter, no assignee, no comments -- the best minimisation posture in
the catalog. And `robots.txt` is `User-agent: * / Disallow: /` with an allowlist
of six CGI paths, none of them `/rest/`. The file is **curated, not boilerplate**
-- it allows `/show_bug.cgi` while disallowing `/show_bug.cgi*ctype=*`.

**A CONTENT LICENCE IS NOT AN ACCESS GRANT**, and Mission 1.18 established that
separation for Stack Exchange, where the API Terms supplied what the licence did
not. TDF publishes no API terms and its only access statement is negative. **This
is the first time the two-layer rule blocked a source whose licence was
perfect.**

**LAUNCHPAD CARRIES TWO INDEPENDENT BLOCKERS**, and the second is the durable
one. Its *Bugs copyright* grants tracker metadata *"freely for any purpose"* while
leaving comments with their authors -- splitting exactly where this mission's
minimisation does. But its robots file disallows `/api/`, names **ClaudeBot,
Claude-User and Claude-SearchBot**, and sets `Content-Signal: ai-input=no`; and
its API returned **41 fields including `owner_link` with a field allowlist
ignored**, so the relation cannot be acquired without fetching a person link and
discarding it. Permission can change with a message; an API's field model cannot.

**TWO PROCESS FAILURES OF OURS, BOTH DISCLOSED.** Two metadata-only probes
reached TDF's `/rest/` **before** its robots.txt was read -- wrong order, no
request after the reading, nothing persisted, and the corrective rule is that
robots.txt is read before the first probe. And the two candidates were briefly
registered in the catalog before it emerged that **a registered source must carry
a LEGACY-profile review**: eighteen tests and two generated documents assume one,
and these were assessed only under `local-private-research-v1`. The registration
was reverted rather than made to fit, because making the legacy review optional
catalog-wide is an architectural change that belongs in its own mission with an
ADR. The two sources were also removed from the local database, with the FK
closure read first and the blast radius counted: 2 sources, 2 access profiles, 9
capabilities, 6 evidence rows, 2 reviews, 2 coverage rows, and **every research
table unchanged**.

**Two 1.20 wordings corrected first.** Its Docker root-cause descriptions are
ANALYST readings rather than source-native facts, and no deterministic step
produced them. And *"not fixable by narrowing further"* claimed more than 89
questions can carry: the wording is now the project decision it actually is.

**CONSEQUENCE: BOTH DETERMINISTIC ROUTES ARE EXHAUSTED** -- text-derived identity
broad (1.18) and narrow (1.20), and source-native identity here -- so **Mission
1.22 should be Semantic Problem Equivalence / INFERRED Claims V1**, which arrives
with its difficulty measured rather than assumed. No inference was started, no
operator was contacted, and no existing source was touched

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
- docs/data/model-inference-execution-governance-v1.md (added in 1.46)
- docs/data/problem-equivalence-evaluation-v1.md (added in 1.47)
- docs/data/problem-family-rubric-v1.md (added in 1.49)
- docs/data/problem-family-human-reference-v1.md (added in 1.51)
- docs/data/opportunity-engine-foundation-v1.md (added in 1.54)
- docs/data/opportunity-synthesis-egress-governance-v1.md (added in 1.55)
- docs/data/targeted-evidence-completion-v1.md (added in 1.56)
- docs/data/canonical-subject-registry-v1.json (added in 1.56)
- docs/data/answer-acceptance-semantics-v1.md (added in 1.59)
- docs/data/commercial-dimension-source-feasibility-v1.md (added in 1.60)
- docs/data/observation-scope-rules-v1.json (added in 1.61)
- docs/data/scope-relation-registry-v1.json (added in 1.61)
- docs/data/docker-commercial-scope-mapping-v1.md (added in 1.62)
- docs/data/docker-evidence-reliability-review-packet-v1.md (added in 1.63)
- docs/data/docker-reliability-operator-decisions-v1.md (added in 1.64)
- docs/data/docker-diagnostic-aggregation-v1.json (added in 1.65)
- docs/data/evidence-aggregation-calibration-strategy-v1.md (added in 1.66)
- docs/data/calibration-reference-dataset-schema-v1.json (added in 1.66)
- docs/data/second-pilot-selection-v1.json (added in 1.67)
- docs/data/proposition-convergence-contract-v1.md (added in 1.68)
- docs/data/second-pilot-ted-category-selection-v1.json (added in 1.69)
- docs/data/second-pilot-convergent-reliability-review-packet-v1.md (added in 1.71)
- docs/data/human-reliability-assessment-rubric-v1.md (added in 1.72)
- docs/data/second-pilot-convergent-operator-reliability-review-v1.md (added in 1.73)
- docs/data/wikimedia-convergent-reliability-review-packet-v1.md (added in 1.76)
- docs/data/wikimedia-convergent-operator-reliability-review-v1.md (added in 1.77)
- docs/data/ted-eu-official-reuse-response-v1.md (added in 1.78)
- docs/data/independent-statistical-route-feasibility-v1.md (added in 1.79)
- docs/data/cross-apparatus-convergence-feasibility-v1.md (added in 1.80)
- docs/data/falsifiable-evidence-apparatus-requirements-v1.md (added in 1.81)
- docs/data/source-independent-claim-semantics-v1.md (added in 1.82)
- docs/data/deterministic-inferred-claim-contract-v1.md (added in 1.83)
- docs/data/deterministic-derivation-provenance-schema-v1.md (added in 1.84)
- docs/data/deterministic-inferred-evaluator-foundation-v1.md (added in 1.85)
- docs/data/refusal-derivation-binding-design-v1.md (added in 1.86)
- docs/data/refusal-provenance-schema-v1.md (added in 1.87)
- docs/data/deterministic-evaluation-persistence-orchestration-v1.md (added in 1.88)
- docs/data/first-deterministic-inferred-pilot-manifest-v1.md (added in 1.89)
- docs/data/first-deterministic-inferred-pilot-v1.md (added in 1.89)
- docs/data/independence-capable-route-feasibility-v1.md (added in 1.90)
- docs/data/apparatus-search-broadened-v1.md (added in 1.91)
- docs/data/internet-wide-service-presence-route-gate-closure-v1.md (added in 1.92)
- docs/data/observation-addressable-apparatus-contract-v1.md (added in 1.93)
- docs/data/observation-addressable-scanner-pair-selection-v1.md (added in 1.93)
- docs/data/anchor-lineage-review-v1.md (added in 1.94)
- docs/data/anchor-operational-reviewability-v1.md (added in 1.94)
- docs/data/partner-documentation-recovery-v1.md (added in 1.94)
- docs/data/anchor-lineage-and-documentation-closure-v1.md (added in 1.94)
- docs/data/anchor-technical-lineage-enquiry-v1.md (added in 1.94)
- docs/data/anchor-operational-methodology-v1.md (added in 1.95)
- docs/data/anchor-sampling-frame-review-v1.md (added in 1.95)
- docs/data/anchor-vantage-review-v1.md (added in 1.95)
- docs/data/anchor-port-window-review-v1.md (added in 1.95)
- docs/data/partner-package-completion-v1.md (added in 1.95)
- docs/data/anchor-operational-closure-and-partner-packages-v1.md (added in 1.95)
- docs/data/netlas-indices-port-window-review-v1.md (added in 1.96)
- docs/data/onyphe-datascan-temporal-object-review-v1.md (added in 1.96)
- docs/data/onyphe-scanned-port-review-v1.md (added in 1.96)
- docs/data/onyphe-full-fidelity-retention-review-v1.md (added in 1.96)
- docs/data/anchor-a8-recomputed-v1.md (added in 1.96)
- docs/data/onyphe-package-recomputed-v1.md (added in 1.96)
- docs/data/qualified-apparatus-readiness-v1.md (added in 1.96)
- docs/data/mission-1.61-enquiry-reassessment-v1.md (added in 1.96)
- docs/data/anchor-enquiry-dispatch-review-v1.md (added in 1.97)
- docs/data/onyphe-datascan-record-lifecycle-v1.md (added in 1.97)
- docs/data/onyphe-datascan-port-configuration-v1.md (added in 1.97)
- docs/data/onyphe-post-30d-field-retention-v1.md (added in 1.97)
- docs/data/onyphe-package-final-recompute-v1.md (added in 1.97)
- docs/data/apparatus-readiness-after-enquiry-dispatch-v1.md (added in 1.97)
- docs/data/anchor-enquiry-manual-dispatch-packet-v1.md (added in 1.97)
- docs/data/mission-1.65-baseline-v1.md (added in 1.98)
- docs/data/onyphe-technical-methodology-enquiry-v1.md (added in 1.98)
- docs/data/outbound-dispatch-envelope-contract-v1.md (added in 1.98)
- docs/data/netlas-dispatch-envelope-v1.md (added in 1.98)
- docs/data/onyphe-dispatch-envelope-v1.md (added in 1.98)
- docs/data/dual-enquiry-readiness-v1.md (added in 1.98)
- docs/data/onyphe-enquiry-dispatch-packet-v1.md (added in 1.98)
- docs/data/mission-1.66-baseline-v1.md (added in 1.99)
- docs/data/onyphe-enquiry-dispatch-execution-v1.md (added in 1.99)
- docs/data/approved-dispatch-execution-v1.md (added in 1.99)
- docs/data/onyphe-manual-dispatch-attestation-v1.md (added in 1.100)
- docs/data/mission-1.66.2-baseline-v1.md (added in 1.101)
- docs/data/onyphe-public-documentation-reconciliation-v1.md (added in 1.101)
- docs/data/onyphe-temporal-object-public-doc-review-v2.md (added in 1.101)
- docs/data/onyphe-datascan-port-configuration-public-doc-review-v2.md (added in 1.101)
- docs/data/onyphe-user-api-configuration-surface-review-v1.md (added in 1.101)
- docs/data/onyphe-retention-public-doc-review-v2.md (added in 1.101)
- docs/data/onyphe-contact-channel-reconciliation-v1.md (added in 1.101)
- docs/data/onyphe-three-question-reassessment-v1.md (added in 1.101)
- docs/data/onyphe-package-recomputed-v2.md (added in 1.101)
- docs/data/qualified-apparatus-readiness-v3.md (added in 1.101)
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