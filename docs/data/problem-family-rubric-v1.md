# Problem-Family Rubric V1 — a second relation, not a looser first one

**Authoritative for the RELATION.** Mission 1.25 §3, contract
`problem-family-rubric@1.0.0`.

> **Mission 1.24's exact relation stays intact and unweakened.** It was evaluated,
> it did not reach production, and nothing here redefines it, relaxes it, or
> reinterprets its result. This is a **different question** asked for a different
> purpose, and the two are kept apart in code, in provenance and in every
> proposition either can produce.

---

## 1. Two relations, and why one could not become the other

| | `EXACT_ACTIONABLE_EQUIVALENCE` | `SAME_PROBLEM_FAMILY` |
|---|---|---|
| asks | would the working fix for A tell a reader what to change for B? | are A and B blocked on substantially the same thing? |
| answerable by | someone who knows the fix | someone who knows the problem domain |
| serves | duplicate detection, debugging | opportunity research |
| status | evaluated, **not production-ready** | this mission |

**Mission 1.24 discovered that its own relation was hard to label**, and the
reason is structural rather than a labelling failure: *would the fix transfer?*
requires knowing the fix, and the reviewer of a public Q&A corpus usually does
not. That is a real limitation of the relation for this purpose, and loosening
its threshold would not have addressed it — the question would still have needed
the same expertise, just answered more permissively.

**So the relation changed rather than its threshold.** The family question is
answerable from published text by someone who understands what people are trying
to do, which is the judgement an opportunity researcher actually makes.

---

## 2. The granularity, fixed once

> Two published observations belong to the SAME PROBLEM FAMILY when they describe
> substantially the same user problem, pain or blocked goal — at a level where one
> product, tool, documentation change or workflow could reasonably help both
> people — even if the technical root causes differ and even if the fixes differ.
>
> Ask: **what was each person trying to do, and what stopped them?** If the
> answers are substantially the same thing, it is one family. If one intervention
> would have to be two unrelated interventions to help both, it is not.

**Three outcomes**, with `ABSTAIN` mandatory: `SAME_PROBLEM_FAMILY`,
`DIFFERENT_PROBLEM_FAMILY`, `ABSTAIN`. Where the text does not establish what a
person was trying to do, the answer is ABSTAIN — which is a judgement about the
text, not a refusal to work.

---

## 3. What is insufficient, which is the load-bearing half

The corpus is 89 Docker questions. A relation satisfied by shared technology
would return SAME for everything and mean nothing, so this list is longer than
the qualifying rule and each entry is insufficient **by construction** rather
than below a threshold. A threshold invites *how much shared symptom is enough*,
and the answer is that no amount is.

- the same tool, runtime or platform
- the same site tags, however specific
- the same language, framework or base image
- **the same wrapper or harness diagnostic, however long the shared string** —
  Mission 1.20's three questions share 106 characters of exact runc output and
  are three unrelated blocked goals
- the same generic error class — permission denied, connection refused, exit code
  1, HTTP 500, a bare `ValueError`, *the build failed*
- **the same broad category of component** — two database connectivity failures
  are not one family merely because both involve databases
- the same lifecycle phase alone — *both happen at build time* is a coordinate,
  not a goal

---

## 4. The worked examples, and what each is for

**Qualifying — `78089171` with `78098380`, a real corpus pair.** A Next.js
`NEXT_PUBLIC_` variable undefined in a Kubernetes pod, and `docker-compose`'s
`env_file` absent during a Dockerfile build. Mission 1.24 classified this
DIFFERENT under the exact relation and both readings were defensible there, since
the components genuinely differ. Under this relation it is clear: each person is
trying to get a configuration value into a place that reads it, and each is
defeated by the same thing — **the value is supplied at one lifecycle phase and
needed at another**. One piece of documentation or one tool that said *this
variable is read at build time and set at run time* would help both.

**Non-qualifying — the runc pair.** 106 characters of identical daemon output,
then a file-mode problem on a script the image contains versus a binary the image
does not contain. The shared string is what the daemon prints when anything fails
at that step, so it describes the machine's reporting rather than either person's
problem. **A wrapper is never a family**, and this example exists so that rule is
not left to judgement.

**Non-qualifying illustration — databases.** A container that cannot reach
MongoDB, and a Spring Boot container refused by SQL Server under integrated
security. Both are databases in containers emitting connection failures; the
blocked goals are network reachability and Windows authentication, and no single
intervention addresses both.

**Borderline, and decided — `78093369` with `78105004`.** Both are *my Docker
build fails while installing a dependency*, both end in `exit code: 1`, and a
tool that explained failed package installs would arguably help both. **Decided
DIFFERENT**, because that framing is too broad to be useful: it makes every
failed build one family and the resulting opportunity is *make builds work*. A
family must be narrow enough that one intervention is describable.

**Abstention — `78097071` with `78096175`.** One side reports no blockage at all,
so there is nothing to compare a blocked goal against. ABSTAIN rather than
DIFFERENT: DIFFERENT asserts the goals are distinct, when one was never
established.

---

## 5. What a family judgement never means

Written as data in `relations.py` and asserted by tests, because each is a
sentence somebody will otherwise write:

    SAME_PROBLEM_FAMILY  =/=>  EXACT_ACTIONABLE_EQUIVALENCE
    SAME_PROBLEM_FAMILY  =/=>  same root cause
    SAME_PROBLEM_FAMILY  =/=>  same fix
    SAME_PROBLEM_FAMILY  =/=>  the same bug
    SAME_PROBLEM_FAMILY  =/=>  permission to merge records
    SAME_PROBLEM_FAMILY  =/=>  a source-native duplicate

And, separately from the relation itself: a family Signal establishes **no**
market size, willingness to pay, commercial viability, product demand, count of
distinct users, or revenue potential. Author identity was never acquired, so no
count of people is available now or ever. Those propositions need convergence
with other evidence families, which is why this mission exists before that one.

A Signal derived from this relation may say exactly one thing:

> Under `problem-family-rubric@1.0.0`, observations X and Y were classified as
> belonging to the same recurring problem family.

**Pairwise only. No transitive closure**: A~B and B~C do not give A~C without
evaluating that pair.

---

## 6. Candidate generation: measured, not assumed

`docker-lexical-candidates@1.0.0` **is not too narrow** for this relation. It
qualifies 731 of 3 916 possible pairs, reaches 84 of 89 observations, and
surfaced the one pair Mission 1.24's reference called SAME — by shared tags, with
no shared title token and no shared diagnostic.

**Its ordering was wrong, which is a different defect.** It scores a shared
diagnostic by raw character length, correct for exact equivalence and close to
worthless here. Under it the runc trio ranked 1–3 and the family-shaped pair
ranked 39.

So `docker-problem-family-candidates@1.0.0` **reuses the qualifying predicate
unchanged** — imported rather than restated, with a test asserting both relations
consider the same 731 pairs — and versions only the ordering:

- the **rarest** shared tag by corpus inverse-document-frequency, not the sum.
  Summing rewards sharing a whole stack, which §3 lists as insufficient; measured
  on the corpus, the summing variant ranked the family-shaped pair 315th.
- a small weight per shared title token.
- **a shared diagnostic weighs zero.** Not a small constant: a small constant
  claims it contributes a little, and Mission 1.20 refutes that. At zero the runc
  trio falls to rank 239, which is where a wrapper belongs when the question is
  about goals.

**And the honest limit, stated rather than hidden: rarity measures specificity,
not concern.** `github` and `docker-desktop` are rare and name technologies;
`environment-variables` is rare and names a concern. Nothing lexical separates
them without a hand-written list of concern tags — a judgement nobody reviewed
and wrong on the next corpus. So the top of the ordering is a **mix**, and
separating concern-shaped from stack-shaped pairs is the reviewer's job. That is
what *worth asking about* means.

---

## 7. The acceptance criterion, frozen before any prediction

`family-v1-positive-coverage-and-false-positive-avoidance`. The classifier passes
only if **all** of the following hold on the scored split:

| | |
|---|---|
| labelled pairs | ≥ 8 |
| pairs the reference calls SAME_FAMILY **in that split** | ≥ 2 |
| false `SAME_PROBLEM_FAMILY` | **0** |
| **true `SAME_PROBLEM_FAMILY`** | **≥ 1** |

**The last row is what Mission 1.24 lacked.** Without it a classifier answering
DIFFERENT to everything — or ABSTAIN to everything — records zero false positives
and passes, which is exactly what happened and why that evaluation established
nothing. Requiring a demonstrated positive makes both constant classifiers fail
by construction, and `AcceptanceCriterion.defeats_a_constant_classifier` computes
that property from the numbers rather than asserting it in prose.

**Abstention is still never counted as an error**, because the alternative to an
abstention is a guess. But abstaining on *every* positive now fails the true-SAME
clause. That is the honest price of caution: free when it is caution, not free
when it is a refusal to ever commit.

**No accuracy, precision or recall figure is a pass condition.** A proportion over
a few dozen pairs has an interval wider than any difference it could show.

---

## 8. What has not happened yet

No family classification has been run. No model has seen any pair under this
rubric. The prompt is written once and frozen before the reference labels are
scored, and the holdout is run once against it. No production inference, no
Signal, no Claim, no Evidence — and if the labelled batch turns out to contain no
defensible positives in the scored split, **`EVALUATION_INSUFFICIENT` is the
result and the rubric will not be widened to manufacture one.**
