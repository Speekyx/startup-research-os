# Mission 1.29 — Opportunity Synthesis Egress Governance V1

**Outcome: `OPPORTUNITY_SYNTHESIS_EGRESS_PARTIALLY_READY`.**

Three of the four source families that contribute canonical Evidence now have a
transmission decision. The fourth was assessed, and its decision could not be
recorded without breaking something Mission 1.29 §0 forbids breaking.

| | |
|---|---|
| sources assessed | **4** |
| decisions recorded in the registry | **3** |
| packets egress-authorized | **8 of 9** |
| packets formable | **0 of 9** (unchanged) |
| model calls / cost | **0 / 0.00 USD** |
| Opportunities created | **0** |
| canonical counters | **unchanged** |
| authorizable (source, profile) pairs | **8 before, 8 after** |
| tests | **108** in the engine package, 1629 in acquisition, 0 failures |

---

## §16 — The four assessments

### WIKIMEDIA PAGEVIEWS — `PERMITTED`

**Representation:** article identifiers, aggregate request measurements, the
derived Claim, source attribution.
**Conditions:** none, and that is a decision rather than an omission.
**Basis:** CC0 1.0, named by the operator's own access policy under a heading
reading *Data licensing*. Section 2 waives all Copyright and Related Rights —
including database rights under Directive 96/9/EC **by name** — *"for any purpose
whatsoever, including without limitation commercial"*. There is no act left for a
licence to restrict.
**No attribution condition was written**, because CC0 creates no attribution
obligation and Mission 1.19 established that writing one would leave a reader
unable to tell a duty from a habit.
**Unresolved:** bulk-dumps payloads are not assessed; that route is refused by
name and no such payload is held.

### WORLD BANK — `PERMITTED_WITH_CONDITIONS`

**Representation:** indicator id, geography, period, numeric value, the derived
Claim, attribution.
**Condition:** **CC-BY-4.0 only**. Acquisition authorises CC-BY-4.0 *or*
ODbL-1.0; this decision covers the first alone.
**Basis:** the CC BY 4.0 legal code, retrieved for this mission rather than the
summary page the existing review rested on. Section 2(a)(1) grants *"reproduce
and Share"* — two acts, so reproduction stands alone. Section 1 defines Share as
providing material *"to the public"*, and a contracted processor is not the
public. Section 3(a)(1) triggers attribution only on Sharing. Section 4 grants
extraction and reuse where database rights apply, so unlike TED there is no open
database-right question.
**Unresolved:** whether transmission is Sharing (nothing rests on it); whether
ODbL would permit it (NOT ADDRESSED, and no ODbL resource is held).

### GDELT — `PERMITTED_WITH_CONDITIONS`

**Representation:** the aggregate lexical measurement, corpus and stream
identifiers, periods, the derived Claim.
**Prohibited representation:** article bodies, headlines, publisher-attributed
text, article URLs.
**Condition:** the citation obligation, which is **live here and not elsewhere**.
**Basis:** GDELT's terms grant *"unlimited and unrestricted use for any academic,
commercial, or governmental use of any kind"* and permit redistribution *"in any
form"* — which contains a transmission comfortably. But the grant's **subject** is
datasets *the GDELT Project releases*, and that is what bounds it.
**Unresolved:** transmission of third-party article text is NOT ADDRESSED and
prohibited. No article text is held, so the bound constrains a future collector.

### TED — assessed `UNCLEAR`, and **not recorded in the registry**

**Representation:** would have been the derived canonical one; raw notice payload
prohibited either way.
**Conditions:** unchanged; all four survive, verified.
**Unresolved:** H-36A NOT ESTABLISHED, H-36B NOT ADDRESSED, and now **H-39**.

The full reasoning is in `opportunity-synthesis-egress-governance-v1.md` §7.
The short version is below, because it is the mission's most useful finding.

---

## The finding: recording a decision is not free

Recording TED's `UNCLEAR` required appending local review v3. Appending one
**orphans the operator's acceptance** of
`ted-database-right-residual-exposure-accepted`, because a verification is pinned
to the review version it was recorded against — deliberately, since a re-review
can change what a condition means.

That condition is `HUMAN_CONFIRMATION`. **No verifier in this repository may
satisfy one, by design.** So there is no re-check available: only the operator
can restore it.

**This was verified against the real deployment, not predicted.** With v3 in
place, `build_authorization('ted-eu')` raised
`review conditions not satisfied: ted-database-right-residual-exposure-accepted`,
and TED stopped being acquirable.

Mission 1.29 §0 says: *"Do not rewrite source acquisition eligibility merely
because model transmission is being assessed. These are separate questions."*
Flipping TED from acquirable to not-acquirable **as a side effect of assessing
egress** is exactly the collapse that sentence exists to prevent. The append was
withdrawn; TED's review line is untouched at v2.

**Nothing operational was traded away.** `NOT_ASSESSED` and `UNCLEAR` both refuse
at the runtime gate. What the registry loses is the *distinction*, and the
governance document carries it instead, with H-39 named and the exact operator
acceptance sentence written down — and, exactly as Mission 1.15.6 did, **writing
it down is not recording it.**

**The asymmetry is the general rule.** The other three sources' conditions are all
CAPABILITY-verified, so a version bump costs a re-check and nothing else. TED's
rests on a human acceptance. **A source whose approval rests on a human decision
is a source whose review cannot be cheaply amended**, and that cost is invisible
until a mission tries.

---

## §0 and §1 — What was preserved

The four governance dimensions stayed independent. `model_processing` was not
read as implying transmission; acquisition permission was not read as implying
either; no provider authorization was broadened; the profile's
`external_model_egress` was not touched.

**The version bump was made honest rather than assumed honest.** For each of the
three recorded sources, the append script asserts that `required_conditions` and
every other activity assessment are **byte-identical** to the previous version,
and refuses otherwise. A separate re-check script asserts the same thing again
before advancing each compliance pin. A test asserts it a third time, over the
committed catalog.

**The Mission 1.23 hazard fired, exactly as designed.** Appending the reviews
stalled the compliance pins and dropped authorizable pairs from 8 to 5; the
re-check restored them to 8. Confirmed by stashing the change and re-running:
**8 before, 8 after, no net change.** My first regression check read only the
catalog and would have missed this — the compliance configuration is a separate
pin, and that is worth knowing next time.

---

## A refusal reason that was wrong

`InferenceRefusalReason` had a code for `NOT_ASSESSED` and one for a refusal.
`UNCLEAR` and `NOT_ADDRESSED` had none and fell through to
`SOURCE_EXTERNAL_MODEL_TRANSMISSION_REFUSED` — telling an operator a reviewer
decided against them when a reviewer decided the question needs a human.

`SOURCE_EXTERNAL_MODEL_TRANSMISSION_UNRESOLVED` was added, and the packet gate
reports `UNRESOLVED` rather than `REFUSED`. **An operator can close an open
question and cannot argue with a decision.** The same argument ADR-033 made for
`NOT_ASSESSED`, one state further along. TED was the first source to reach that
branch — and, after the withdrawal, is currently reported as `NOT_ASSESSED`
again, so the new code is exercised by tests rather than by the live corpus.

---

## §3 and §9 — The representation, bounded in code

`opportunity-transmission-representation@1.0.0`. The payload carries nine
top-level keys and **no raw source payload at all**: no collected record, no API
response body, no article text, no notice payload, no personal data. Only
`claims` and `subject` carry anything source-derived, and both are canonical
sentences this repository composed.

The bound is an **allowlist**, not a denylist: an unrecognised key refuses,
because a denylist is a list somebody must remember to extend and the field
nobody remembered is the one that leaks. `serialize_packet_for_model` calls the
check on the assembled payload and **raises rather than trimming** — a trimmed
payload is a different packet from the one the decision authorised.

One fail-open was found and fixed while writing it: the deep scan tested
`isinstance(dict)` while the signature accepted any `Mapping`, so a non-dict
mapping would have returned no paths at all.

---

## §11 — The rerun

Deterministic path only, no synthesis.

| | before 1.29 | after 1.29 |
|---|---|---|
| `AVAILABLE_FOR_EXTERNAL_SYNTHESIS` | 0 | **8** |
| `UNAVAILABLE` | 9 | **1** (TED) |
| `HYPOTHESIS_FORMABLE` | 0 | **0** |
| model calls | 0 | **0** |
| Opportunities | 0 | **0** |

**Egress authorization made no packet formable, and that is the design working.**
Permission to send is not evidence. The three Wikimedia packets still carry one
counting dimension each; the TED packet still holds one row. A test asserts the
two gates stay separate.

---

## §14 — Tests

**26 new tests** in `test_transmission_governance.py`, covering: an explicit
decision per source; decisions scoped to the use profile and to the processing
purpose; missing decisions failing closed; bounded representations; the GDELT
aggregate/article-text distinction; TED's conditions and open questions intact;
training, fine-tuning and embeddings still prohibited; no source review naming a
provider; provider approval not inferred from source approval and the reverse;
personal-data minimisation; authorization before serialization; no model call; no
Opportunity; counters unchanged.

**Three existing tests were repaired, none weakened.**

Appending all four reviews initially broke ten, and **withdrawing the TED append
reverted seven of them cleanly** — they pinned TED version numbers that went back
to what they were. That is worth stating rather than quietly banking: the number
of tests a change breaks is a measure of the change, and this one got smaller
when the change did.

The three that remained:

- Two used `world-bank` as the example of *a review written before this activity
  existed reads as NOT_ASSESSED*. Still true — of **v1**, which they now name
  explicitly. Stricter than before, because they no longer depend on "current"
  happening to be unassessed. One of them moved to `eurostat`, which still has an
  unassessed transmission activity and so still isolates the two fields.
- One asserted the five aligned sources' local reviews were *version 1*. It now
  asserts the local **line starts at 1** and that Mission 1.17 wrote its first
  entry, which is the cross-profile isolation property it was actually
  protecting.

Totals: 108 in the engine package, 1629 in acquisition, 571 zero-dependency, all
pytest suites across 9 packages, 0 failures. Nine validators, four generated-doc
`--check` steps, ruff, ruff format, mypy, both CI greps, `migrate --plan` pass.

---

## §15 — Counters

| | Before | After |
|---|---|---|
| RawRecords / NormalizedRecords | 148 / 148 | **148 / 148** |
| Signals / Claims / ClaimRevisions / Evidence | 26 / 26 / 26 / 26 | **26 / 26 / 26 / 26** |
| ReliabilityAssessments | 1 | **1** |
| Opportunities / Embeddings / Scores | 0 / 0 / 0 | **0 / 0 / 0** |
| Registered sources | 29 | **29** |

**Governance records changed, and only those:** three local review versions
appended (wikimedia-pageviews v2, world-bank v2, gdelt v2), three compliance pins
advanced after a performed re-check, two new evidence rows, four new open
questions. One orphaned `ted-eu` v3 row created by an intermediate load was
removed from the dev database under a guard that read the FK closure first and
refused unless it could show the operator's acceptance was **not** attached to it.

---

## §16 — The eight questions

1. **Packets egress-authorized?** **8 of 9.**
2. **Blocked by governance?** **1** — the TED packet.
3. **Blocked by evidence sufficiency?** **9** — all of them, unchanged.
4. **Any formable?** **No.**
5. **Model calls?** **None.**
6. **Opportunities created?** **None.**
7. **Scoring?** **None.**
8. **Problem-family inference still PARKED?** **Yes**, untouched.

---

## §17 — Outcome

**`OPPORTUNITY_SYNTHESIS_EGRESS_PARTIALLY_READY`.**

Not A, because TED has no usable authorization path and would need an operator
act. Not C, because three families do. And **explicitly not
`OPPORTUNITY_ENGINE_READY_TO_GENERATE`**: every packet remains
`HYPOTHESIS_INSUFFICIENT_EVIDENCE`, which is a separate gate this mission did not
touch and did not try to.

---

## §18 — Recommended next mission

**Targeted evidence completion for subjects already in the packets.** Not broad
source expansion: the corpus fails on breadth per subject, not on volume.

The two shapes worth closing, in order of how close they are:

- **The Wikimedia subjects** (`Docker_(software)`, `Podman`, `Kubernetes`) each
  hold six rows and one counting dimension, `AUDIENCE_OR_USAGE`. They need **one
  genuinely different dimension** for the same subject. They are now
  egress-authorized, so nothing governance-side stands in the way.
- **The TED subject** (CPV division 90) holds three commercial dimensions and
  **one row**. It needs a second independent Evidence row. Note that this subject
  is the one still blocked at the egress gate, so evidence work there buys a
  formable packet and not a synthesizable one until H-39 closes.

**Do not decide the acquisition source before inspecting current coverage,
governance and available collectors.** Six of eight demand-side evidence families
still have no approving source, and picking a target without re-reading that is
how a mission discovers at the end that its chosen source is `RESTRICTED`.

An operator act is also available and cheap, independently: closing **H-39** by
recording the acceptance sentence in
`opportunity-synthesis-egress-governance-v1.md` §7 would move TED to a recordable
decision — in a mission that owns TED and re-records the acceptance against the
new review version, in that order.

**Do not start scoring or ranking.** Nothing about this mission moved the
sufficiency gate, and D-03 still blocks scoring for reasons this mission did not
touch.
