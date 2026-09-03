# Mission 1.31 — First Bounded Opportunity Synthesis V1

**Outcome: `OPPORTUNITY_SYNTHESIS_OUTPUT_REJECTED`.**

The first real synthesis ran. The model returned `FORM_HYPOTHESIS` with a
careful, bounded, well-cited hypothesis, and **the frozen persistence gate
refused it on exactly one clause — which is a defect in my audit, not an
over-reach by the model.**

**No Opportunity was persisted. Opportunities remains 0.**

| | |
|---|---|
| packet | `subject:docker`, 7 rows, 2 families, 2 counting dimensions |
| egress | `AVAILABLE`, resolved **before** serialization |
| logical calls | **1** (+ 1 retry permitted, **0** used) |
| abandoned attempts | **2**, on an under-sized output cap — see below |
| tokens | 5 967 in / 2 632 out |
| **cost** | **0.0383 USD** (+ ~0.041 abandoned) against a **0.25** ceiling |
| Opportunities created | **0** |
| canonical counters | **unchanged** |

---

## §24 — The twenty-four questions

**1. Packet?** `subject:docker`, packet
`c25451c569909207357d0af19698e4737b7c85961fcf393bf632ba8b8242110e`.

**2. Evidence IDs.** All seven, and the model cited all seven:
`13a5eadb…2074`, `16a8c39c…9cae`, `1b93db71…7bc49`, `487f62c6…0003`,
`516182ff…8a75`, `6cf92ad6…430b`, `f1e0b7a4…dce1`.

**3. Claim IDs.** `565bbcb7…a230`, `6e4c3f21…c4b5`, `05cac6f6…c774`,
`c58949e4…b7c0`, `b3d0d2d0…1b03`, `459e9fec…9bc5`, `1829e497…5ccf7`.

**4. Dimensions supported.** `AUDIENCE_OR_USAGE`, `PROBLEM_OR_NEED`.

**5. Dimensions unsupported.** All eleven §6 required, and the model reported
every one: `RECURRENCE_OR_FREQUENCY`, `ECONOMIC_VALUE`, `WILLINGNESS_TO_PAY`,
`BUYER_OR_BUDGET_EXISTENCE`, `MARKET_ACTIVITY`, `SOLUTION_GAP`,
`SOLUTION_DISSATISFACTION`, `COMPETITIVE_SUPPLY`, `DISTRIBUTION_SIGNAL`,
`REGULATORY_OR_STRUCTURAL_DRIVER`, `FEASIBILITY_SIGNAL` — plus `TREND_OR_CHANGE`
unprompted.

**6. Representation transmitted.** `opportunity-transmission-representation@1.0.0`,
unbroadened: exactly the nine permitted keys, 4 151 characters. No raw record, no
API response, no question body, no article text, no personal data.

**7. Authorization before serialization?** **Yes.** The egress gate resolved
`AVAILABLE` and `serialize_packet_for_model` was called only after it.

**8. Route.** `anthropic` / `claude-sonnet-5`, tier `STRONG_MODEL`, the existing
approved route. Nothing hard-coded.

**9. Calls?** **1.** **10. Retries?** **0** on the accepted call; 2 attempts were
abandoned earlier (below). **11. Tokens?** 5 967 / 2 632. **12. Cost?** **0.0383
USD**, plus roughly 0.041 on the abandoned attempts. Total well under 0.25.

**13. Model decision?** `FORM_HYPOTHESIS`.

**14. Did deterministic validation accept it?** **No — on one clause, wrongly.**

**15. Opportunity persisted?** **No.**

**16. Hypothesis statement** (recorded, not persisted):

> Given evidence of (a) day-to-day fluctuation in requests for the
> "Docker_(software)" Wikipedia article and (b) a bounded count of 88 questions
> filed under the "docker" tag on Stack Overflow, it is worth investigating
> whether there exists an underserved information or problem-solving need among
> people encountering the subject "docker" — without any claim as to who these
> people are, why they engaged, whether the same actors recur, or whether any
> commercial response is warranted.

**17. What it does not establish** — the model's own list, which is better than
the one the brief asked for: that a market exists; that anyone would pay; that a
buyer or budget exists; that competitors are weak or a gap exists; that users are
dissatisfied; that adoption is rising or falling; that the counts indicate market
size; that a channel is reachable; that any regulatory driver applies; that the
need is frequent or recurring; that money moves; that the differences represent a
continuing trend; **that the 88 questions represent a shared, well-defined
problem**; and **that the Wikipedia counts represent distinct human readers**.

**18. Unsupported commercial claims persisted?** **None** — nothing was
persisted, and `commercial_claims_supported` came back empty.

**19. Scoring?** No. **20. Ranking?** No. **21. Reliability?** Still unresolved:
all 7 rows `NON_SCORABLE` / `MISSING_RELIABILITY`. **22. Independence?** Still
`UNKNOWN` on all 7. **23. Problem-family?** Still **PARKED**.

**24. Next mission?** Below.

---

## The rejection, and why it is mine

The frozen gate returned exactly one refusal, against
`evidence_bound_reasoning_summary`:

> "No statement in the packet establishes who these actors are, whether any need
> recurred, whether money moved, **whether anyone would pay**, whether a buyer
> exists, **whether competitors already serve this space**, whether any channel
> is reachable, whether any solution gap or dissatisfaction exists, or any
> regulatory driver."

`check_statement` flagged `would pay` and `competitors`. **That sentence is an
enumeration of absences — precisely what §6 and §16 required the model to
produce.** My guard is token-based and cannot see negation, so it read a denial
as an assertion and refused the best paragraph in the output.

This is `testing-strategy.md` §23 in a new place: a scan firing on the text that
obeys the rule. It was caught there by excluding docstrings; the equivalent here
is that a forbidden term under a denial is not an assertion.

**Every other clause of the gate passed.** Cited ids all belonged to the packet;
every Evidence was cited with its Claim; no dimension was over-claimed; all
eleven mandatory unsupported dimensions were reported; independence was preserved
as UNKNOWN; reliability was preserved as NON_SCORABLE / MISSING_RELIABILITY; and
the other three prose fields audited `SUPPORTED`.

### Why the outcome is still C, and why I did not re-run

**§12 says: do not weaken the gate after seeing the answer.** This is a defect
rather than a loosening — but I concluded it was a defect *because* it rejected an
output I judged sound, and that is exactly the reasoning §12 exists to distrust.

So: the run keeps its recorded verdict under `audit@1.0.0`, **no Opportunity is
persisted**, and the outcome is `OPPORTUNITY_SYNTHESIS_OUTPUT_REJECTED`. The
guard was corrected to `opportunity-claim-guard@1.1.0` /
`opportunity-synthesis-audit@1.1.0`, with tests including the exact rejected
sentence, and **the model was not called again**. A re-run belongs to a mission
the operator authorises, not to this one rescuing its own result.

The correction is denial-aware and scoped to one sentence, so
`no evidence establishes willingness to pay. Buyers would pay 40 EUR.` still
fails on the second sentence, and a marker appearing *after* the term does not
clear it.

---

## The other thing that went wrong, and it cost two calls

The first attempt and its one permitted retry **both failed schema validation**,
missing the last five required fields. The cause was mine: `max_output_tokens`
was 1 500, and the 17-field schema's own `maxLength` values admit roughly 5 200
characters before JSON overhead — about 1 800 tokens. **The model never finished
an answer.**

Mission 1.27's lesson was to bound the output so a cost ceiling is real rather
than nominal, and that lesson is intact. What I got wrong is the arithmetic:
bounding below what the requested schema can serialise is a defect, not a
discipline. The cap is now 3 000, computed against the schema, and the hard
maximum recomputed at 0.0713 USD before the call.

**Raising it and re-running is not the retry-shopping §10 forbids**, and the
distinction matters: nothing about the task, prompt, schema or evidence changed —
only a transport bound — and no answer was being rejected in favour of a nicer
one, because no complete answer existed. Both wasted attempts are counted in the
run artifact under `abandoned_attempts_before_output_cap_fix`.

---

## What the model actually did well

Worth recording, because the mission's real question was whether SROS can turn a
packet into a hypothesis **without** unsupported commercial claims.

- It set `target_actor_if_supported` to `UNKNOWN_NOT_SUPPORTED` rather than
  inventing a persona.
- It named the intervention as a *class*, explicitly "not a defined product or
  feature set".
- It restated the Wikimedia measurement as *day-to-day fluctuation*, not growth —
  which is right, and two of the six rows are decreases.
- It reproduced the calendar confounder and the heuristic-requester caveat from
  the supplied bounds.
- It said the question count is "a count of questions, not of people (authors are
  not identified)" and "not evidence the questions share a single problem" —
  independently reaching the boundary Mission 1.27 parked.
- `commercial_claims_supported` is **empty**.
- It listed `TREND_OR_CHANGE` as unsupported without being asked to.

The synthesis path works. The gate that judges it needed one fix.

---

## §22 — Counters

| | Before | After |
|---|---|---|
| RawRecords / NormalizedRecords | 148 / 148 | **148 / 148** |
| Signals / Claims / ClaimRevisions / Evidence | 27 each | **27 each** |
| ReliabilityAssessments | 1 | **1** |
| **Opportunities** | 0 | **0** |
| OpportunityHypothesisRevisions / evidence links | 0 / 0 | **0 / 0** |
| Embeddings / Scores | 0 / 0 | **0 / 0** |
| Registered sources | 29 | **29** |

---

## §19 — Tests

**44 new** in `test_bounded_synthesis.py`, all written and passing **before** the
provider was called: only a formable packet enters synthesis; the package imports
no Gateway or provider; source statements occupy the untrusted region only and
carry their ids as labels; prior knowledge is withdrawn in the prompt; no numeric
confidence; the prompt carries the independence and reliability facts; every
clause of the frozen gate exercised against an output built to violate it (stray
ids, evidence without its claim, over-claimed dimensions, omitted mandatory
report, claimed independence, dropped reliability); the number check; the
world-knowledge check on four sentences that are probably true and were not
supplied; commercial and validation vocabulary; recurrence refused from a question
count; the transmission allowlist unbroadened; and the run artifact's own
honesty.

Seven more were added **after** the run for the corrected guard, including the
exact rejected sentence and the assertion cases that must still fail.

Totals: **189** in the opportunity package, 571 zero-dependency, all pytest suites
across 9 packages, **0 failures**. Ruff, ruff format, mypy, the validators and
`migrate --plan` pass.

---

## §23 and §25 — Outcome and next mission

**`OPPORTUNITY_SYNTHESIS_OUTPUT_REJECTED`**, on a gate defect rather than a model
failure, with the defect fixed and not applied retroactively.

**Recommended next: re-run the bounded synthesis under the corrected guard.**
It is one call, ~0.04 USD, on an unchanged packet and an unchanged prompt hash,
and it is the only thing standing between this repository and its first
Opportunity row. It needs operator authorisation because it re-asks a question
this mission already spent its allowance on.

**Do not build ranking**, whatever that returns. Every one of the seven rows is
`NON_SCORABLE` with `MISSING_RELIABILITY`, so a persisted hypothesis would still
contribute to no score, and D-03 blocks scoring for reasons this mission did not
touch.

If the operator would rather add evidence first, the model's own uncertainty list
is the best brief yet written for it — and the narrowest item on it is
`SOLUTION_GAP` or `SOLUTION_DISSATISFACTION` for the same `docker` subject, since
both are answerable from sources whose governance is already settled and neither
requires the parked relation.
