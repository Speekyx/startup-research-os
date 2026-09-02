# Mission 1.31.1 — Corrected Bounded Opportunity Synthesis Re-run

**Outcome: `FIRST_OPPORTUNITY_HYPOTHESIS_CREATED`.**

The same packet, the same prompt — **byte-identical hash** — and the corrected
deterministic audit. The model returned `FORM_HYPOTHESIS`, every clause of the
frozen gate passed, and **SROS holds its first Opportunity.**

| | Before | After |
|---|---|---|
| RawRecords / NormalizedRecords | 148 / 148 | **148 / 148** |
| Signals / Claims / ClaimRevisions / Evidence | 27 each | **27 each** |
| ReliabilityAssessments | 1 | **1** |
| **Opportunities** | 0 | **1** |
| **OpportunityHypothesisRevisions** | 0 | **1** |
| **Evidence links** | 0 | **7** |
| Embeddings / Scores | 0 / 0 | **0 / 0** |
| Registered sources | 29 | **29** |

One logical call, **0 retries**, 5 967 in / 2 722 out, **0.0392 USD** against a
0.25 ceiling.

---

## §0 — Mission 1.31 is untouched

`opportunity-synthesis-run-v1.json` keeps its outcome, its rejected model output,
its `audit@1.0.0` verdict, its prompt hash, its costs and its abandoned-attempt
record. Mission 1.31 remains `OPPORTUNITY_SYNTHESIS_OUTPUT_REJECTED`. This run
wrote a **new** artifact, `opportunity-synthesis-run-v1.1.json`, and a test
asserts the historical one still reads `audit@1.0.0` / `persist: false`.

---

## §1 — The five required cases, and what running them found

§1 lists five cases that must pass before the provider may be called. Running them
found that **`guard@1.1.0` handled four**.

The fifth — *"Competitors are not established by the evidence."* — was still
flagged, because 1.1.0 only cleared a denial marker appearing **before** its term,
and here the negation is the term's own predicate and follows it.

The two forms are told apart by grammar rather than by order:

| | |
|---|---|
| §1 case 3 | `Competitors **are not** established` — term is the subject, negation is its copula → **clears** |
| §1 case 5 | `Buyers would pay, **which is not** established` — negation in a relative clause behind a comma → **still fails** |

`@1.2.0` adds exactly that one form: `<term> (is\|are\|was\|were\|has\|have\|had)
(not\|never\|no)`, cancelled by an intervening comma or contrastive word.

**This was a pre-call change required by the brief, made before any output for
this run existed.** It is not the shape Mission 1.31 §12 forbids — nothing had
been seen and nothing was being rescued.

### And it surfaced a real off-by-one

Checking the cases exposed a defect in `_phrase_position`: the pattern captures
the character *before* the word so that `supermarket` cannot match `market`, which
makes `match.start()` point one byte early. **Every term not at the start of a
sentence had its tail misaligned**, so `market demand is never established`
cleared while `demand is never established` did not. Fixed to
`match.end() - len(first)`, with a test.

Fifteen cases now pass, including all five §1 requires and the token-boundary case
that made the pattern look that way in the first place.

**Version note, stated rather than glossed:** the brief says to use
`audit@1.1.0`. Because behaviour changed, the constants read **`@1.2.0`**. The
single intended behavioural correction of §11 is unchanged — statements of
absence must not be read as positive assertions — and no other gate moved.

---

## §21 — The twenty-eight questions

**1. Packet unchanged?** Yes.
`c25451c5…2110e`, same 7 Evidence, same 7 Claims, same 2 families, same 2 counting
dimensions.

**2. Prompt unchanged?** **Yes, byte-identical.** `synthesis_prompt_hash()` still
returns `dfd28a0a77e2cae23a268e39eb1c432f23f905810b26dc129f6fd99f7491195e`, the
hash Mission 1.31 recorded. **No prompt tuning.**

**3. Audit version?** `opportunity-synthesis-audit@1.2.0` /
`opportunity-claim-guard@1.2.0`.

**4. Denial-aware tests before the call?** Yes — all five §1 cases plus ten more,
and the full repository suites, before `--apply`.

**5. Egress before serialization?** Yes. `AVAILABLE`, both sources `PERMITTED`,
resolved before `serialize_packet_for_model`.

**6. Route?** `anthropic` / `claude-sonnet-5`, `STRONG_MODEL`.

**7. Calls?** **1.** **8. Retries?** **0.** **9. Tokens?** 5 967 / 2 722.
**10. Cost?** **0.0392 USD** this run; ~0.079 USD across Mission 1.31 and this
one together, including 1.31's two abandoned attempts.

**11. Decision?** `FORM_HYPOTHESIS`.

**12. Evidence cited.** All seven: `13a5eadb…2074`, `16a8c39c…9cae`,
`1b93db71…7bc49`, `487f62c6…0003`, `516182ff…8a75`, `6cf92ad6…430b`,
`f1e0b7a4…dce1`.

**13. Claims cited.** All seven, each paired with its Evidence.

**14. Supported.** `AUDIENCE_OR_USAGE`, `PROBLEM_OR_NEED`.

**15. Unsupported.** All eleven §5 requires, plus `TREND_OR_CHANGE` unprompted —
**twelve**.

**16. Audit pass?** **Yes.** Three prose fields `SUPPORTED`,
`target_actor_if_supported` `NOT_FACTUAL`, none `UNSUPPORTED` or
`BOUND_EXCEEDED`. **17. Refusal?** None.

**18. Persisted?** **Yes.** Opportunity `06113a8b-a83d-423d-8046-18f87d7dbc01`,
revision `efca07a9-b283-473a-887b-a2ae82989bbe`, **7 evidence links**, all at
`ELIGIBLE_CONTEXT`.

**19. The hypothesis:**

> There is evidence worth further investigation that some actors attend to the
> "Docker_(software)" Wikipedia article (with day-to-day request-count
> fluctuations under the platform's own heuristic requester classification) and
> that some actors file public questions tagged "docker" on Stack Overflow within
> a bounded window, indicating at least momentary unserved need at the point of
> asking; whether this reflects any recurring, severe, or commercially
> addressable need, and who the relevant actor is, is not established and would
> require further investigation before any intervention can be scoped.

**20. What it does not establish.** Twelve dimensions marked unsupported, and
five limitations persisted on the revision: every row is `NON_SCORABLE` /
`MISSING_RELIABILITY`; independence is `UNKNOWN` and two families is not two
independent sources; `market_scope` is `GLOBAL` because the column is NOT NULL
and the evidence carries no geography — Ontology V2 §4 defines GLOBAL as the
**absence** of a restriction, not a worldwide-market claim; the question count is
of questions, not people, and not evidence any two share a problem; and two of
the six Wikimedia rows are **decreases**, with the calendar not cancelling.

**21. Unsupported commercial claims persisted?** **None.**
`commercial_claims_supported` came back **empty**.

**22. Reliability?** Unresolved — all 7 rows `NON_SCORABLE`.
**23. Independence?** `UNKNOWN` on all 7. **24. Scoring?** None;
`scoring.scores` does not exist. **25. Ranking?** None. **26. Problem-family?**
**PARKED**, production `NOT_AUTHORISED`.

**27. Counters?** Table above. **28. Next mission?** Below.

---

## §20 — Descriptive comparison with Mission 1.31

Not scored, and 1.31's output is not treated as reference truth.

| | Mission 1.31 | Mission 1.31.1 |
|---|---|---|
| decision | `FORM_HYPOTHESIS` | `FORM_HYPOTHESIS` |
| target actor | `UNKNOWN_NOT_SUPPORTED` | `UNKNOWN_NOT_SUPPORTED` |
| supported dimensions | 2 | 2, identical |
| unsupported reported | 12 | 12, identical |
| `commercial_claims_supported` | empty | empty |
| Evidence cited | 7 of 7 | 7 of 7 |
| audit verdict | `BOUND_EXCEEDED` on one field | all `SUPPORTED` / `NOT_FACTUAL` |
| gate | refused | **accepted** |

**The two outputs agree on every structural judgement.** Both refused to name an
actor, both marked the same twelve dimensions unsupported, both cited all seven
rows, both asserted no commercial claim. What changed is the audit, not the
answer — which is the cleanest available evidence that the Mission 1.31 rejection
really was a guard defect.

The wording differs, as two generations will. This run's is arguably more careful:
it says *"at least momentary unserved need at the point of asking"*, which bounds
the `PROBLEM_OR_NEED` reading to the instant of publication rather than to a
standing condition, and its intervention field declines to name a class at all —
*"the packet itself does not support naming a product, feature, or service
class"*. That is a model refusing to answer part of the question because the
evidence does not reach it.

---

## §17 — Tests

**202** in the opportunity package (13 new for §1's preconditions and the re-run
artifact), 571 zero-dependency, all pytest suites across 9 packages, **0
failures**. Ruff, ruff format, mypy, the validators and `migrate --plan` pass.

**Four TED review tests were repaired, and the precedent was already written in
their own comments.** They asserted `research.opportunities == 0` globally as a
proxy for *this review created nothing*. That count is now legitimately non-zero
on a machine that has run the pipeline and zero on one that has not — the
confusion `testing-strategy.md` §49 forbids a test from encoding, and exactly why
RawRecords and NormalizedRecords were removed from the same assertion in Missions
1.15.7 and 1.15.8. `research.opportunities` has joined them.

The replacement is **stronger, not weaker**: no Opportunity hypothesis cites TED
Evidence, on any machine, however many Opportunities exist. It would fail loudly
if a future mission pulled a TED row into a packet.

---

## §22 — Recommended next mission

**Do not build ranking.** There is one Opportunity and nothing to rank it against,
every supporting row is `NON_SCORABLE`, and D-03 is untouched.

Inspecting the persisted hypothesis, the choice §22 offers resolves clearly
toward **A — targeted commercial evidence completion**, and the hypothesis names
its own priority: *"whether this reflects any recurring, severe, or commercially
addressable need, and who the relevant actor is, is not established"*.

Two of the twelve unsupported dimensions are reachable without the parked
relation and without new governance:

- **`SOLUTION_DISSATISFACTION`** or **`SOLUTION_GAP`** for the same `docker`
  subject. Stack Exchange already publishes, per question, whether the asker
  accepted an answer — held in the corpus today under `answers.has_accepted_answer`
  and deliberately unread. A bounded count of unaccepted questions is one
  derivation over records already held, with the same completeness precondition
  Mission 1.30 established. **Its bound is sharp and must be written first**: an
  unaccepted answer means only that the asker did not accept one, never that the
  problem is unsolved (Mission 1.18).
- **`BUYER_OR_BUDGET_EXISTENCE`** is the most commercially valuable and the least
  reachable: no approving source in the portfolio observes a buyer for developer
  tooling, and TED — the one source that observes buyers — is still egress-blocked
  on H-39 and concerns an unrelated CPV division.

Reliability (option B) is worth naming as second, not first: a reviewed
reliability would make this hypothesis *scorable*, but scoring one opportunity
against nothing produces a number with no comparison class. Breadth before
arithmetic.
