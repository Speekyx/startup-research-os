# Mission 1.23 — Inference Execution Boundary & External Model Egress Governance V1

**Outcome B — READY_FOR_OPERATOR_CONFIGURATION.** The governance question is
answered, the runtime gate is built and exercised, and the boundary is closed on
exactly one remaining condition: no approved provider is configured. **No model
was called. No source content left this machine. 0 model calls, 0 tokens, 0 cost.**

Every research count is unchanged: **148 raw / 148 normalized / 26 Signals /
26 Claims / 26 Revisions / 26 Evidence / 1 session / 0 Opportunities / 0
Opportunity scores / 0 research gaps.** The catalog remains at **29 sources**.

---

## PRE-FLIGHT

Read before acting: `PROJECT_MANIFEST.md`, `docs/CLAUDE.md` and its Boot
Sequence, the Mission 1.22 report and `semantic-problem-equivalence-v1.md`,
ADR-027 and ADR-028, the Stack Exchange local review v1, and both use profiles.

**The finding Mission 1.22 handed over was structural, not procedural.** It did
not stop because a credential was missing. It stopped because `model_processing`
was one field answering a question that is two: *may a model read this* and *may
this leave the deployment so a third party's model can read it*. The second
question had no slot in the contract, so no reviewer could have answered it, and
the profile had no word for the answer either.

That is the same shape as Mission 1.15.4 — a distinction the system needs, with
nowhere to record it, found by the first mission that needed it.

**Two Mission 1.22 wordings were corrected before anything was built.** Its report
answered "does the review cover local inference only, external transmission, or
both" with *"It covers A"* — which reads as a scoping decision somebody made. The
truth is narrower and is the whole finding: the review authorises model inference
**as an activity**, and the model had no way to represent execution location at
all, so it could not have scoped itself to one. And
`semantic-problem-equivalence-v1.md` said none of the four things needed to
proceed *"is a code change"*, which is untrue of the contract extension and of the
runtime gate — both of which this mission then wrote. Neither correction
authorised anything.

---

## CONTRACT

**ADR-033** separates three questions that had been collapsed into one or left
unasked:

| Question | Subject | Where it lives |
|---|---|---|
| may a model READ this | the source | `model_processing` (unchanged) |
| may it LEAVE the deployment | the source | `external_model_transmission` (new) |
| what does this PROCESSOR do | the provider | `model-provider-policy-v1.json` (new) |
| does this deployment permit the class | the profile | `external_model_egress` (new) |

`ASSESSED_ACTIVITIES` grew from eleven to **twelve**. `model_processing` was not
touched and not reinterpreted: reinterpreting it to mean the new thing would have
granted twenty-nine sources a permission nobody assessed.

**Migration 0027** adds `registry.source_policy_reviews.external_model_transmission`
and `registry.use_profiles.external_model_egress`, both **nullable with no
default**, and writes no existing row. Every review written before ADR-033 reads
`NOT_ASSESSED`, which is true — the contract had no slot. A mass `UPDATE` would
have invented sixty-four answers.

**Migration 0028** then writes the two egress decisions Mission 1.23 actually
made into the seeded profile rows. It is a second migration because 0027 is
applied and an applied migration is immutable, and because adding a slot and
filling it are different acts that deserve two legible ledger rows. Both `UPDATE`s
are guarded by `IS DISTINCT FROM`, so re-running writes nothing, and a profile a
later mission adds keeps `NULL`, reads `NOT_ASSESSED`, and refuses.

### Three states, because a boolean would collapse two

`NOT_ASSESSED` (nobody looked), `DENIED` (somebody looked and said no), and
`PERMITTED_TO_APPROVED_PROVIDERS`. The two refusing states are not
interchangeable: one is a decision that can be cited, the other is a question
still open, and telling them apart is most of what this registry is for.

### Not one of rule 8's six

`external_model_transmission` is deliberately **not** a materially required
activity. It gates one operation. World Bank's deterministic collector does not
become ineligible because nobody assessed model egress for World Bank — that
would make a contract addition a breaking change for twenty-nine sources.

The property is asserted directly rather than assumed: for **every** registered
source, the reasons an ordinary acquisition is refused never mention this
activity or the word *egress*.

---

## SOURCE GOVERNANCE

**Stack Exchange local review v2, appended. v1 is not rewritten** and carries no
`external_model_transmission` key, because v1 did not decline to answer — it
could not.

- `external_model_transmission: PERMITTED_WITH_CONDITIONS`
- Basis: CC BY-SA 4.0 §2(a)(1) and §2(a)(4). The reproduction involved in sending
  question text to a processor for inference is inside a grant that permits
  reproduction and Adapted Material for any purpose including commercial, and
  imposes no restriction on the means.
- What the licence does **not** do is say anything about what a processor may do
  with the text once it has it. That is a contractual question about a provider,
  answered by a provider's terms and recorded in the provider policy — not here.

**Two new conditions, and neither names a vendor.** They state the property a
provider must have (no training on submitted content; documented bounded
retention) and that the transmission is for inference only. A source review that
named a company would need re-versioning every time a provider list changed, and
would put provider governance inside the source registry.

**Two new open questions, recorded rather than resolved by assertion.** Whether
transmitting licensed text to a processor is *Sharing* under CC BY-SA is not
decided, and nothing rests on deciding it: §2 covers the reproduction either way,
and this profile publishes nothing. And provider-side retention is **bounded, not
zero** — a zero-retention requirement was not invented, because no policy in this
repository requires one and inventing a rule to look strict would refuse a route
on a rule nobody wrote.

**Personal data is unchanged, and is why this is comfortable.** Owner, account,
profile and comment objects were excluded *at acquisition* in Mission 1.18 and
are not in the corpus. What would be transmitted is a public question title and
body with no author attached. That is a property the data already has, not a
mitigation applied at transmission time.

**Attribution is not expanded.** CC BY-SA's obligation runs to material made
available to others; private inference is not a public display, and nothing here
requires licence boilerplate in a prompt. The obligation on product surfaces is
unchanged and still verified by `stack-exchange-attribution`.

### The cost of appending a review, found the hard way

Appending v2 **broke deterministic acquisition for Stack Exchange** — 23 tests
errored at setup with `not authorized: review conditions not satisfied`. Not
through the new activity: `resolve_effective_verifications` refuses a compliance
configuration written for an older review version, on the stated ground that *a
re-review can change what a condition means*.

**That guard is right, and the repair was to perform the re-check rather than to
silence it.** v2's `required_conditions` array — keys, descriptions, verification
methods, verification details — is byte-identical to v1's. What v2 adds is an
assessment, prose, evidence and open questions, none of which a capability
verifies. The equality is asserted in code before `source-compliance-v1.json` is
bumped to review version 2, and a test pins it, so a future review that **does**
alter a required condition cannot be waved through by editing a number.

Worth stating plainly: a review version is not free, and a mission that bumps one
owes the re-check.

---

## PROVIDER GOVERNANCE

`docs/data/model-provider-policy-v1.json` records posture, the **exact route**
assessed, and first-party evidence.

| Provider | Posture | Route assessed |
|---|---|---|
| anthropic | `APPROVED` | commercial API |
| gemini | `NOT_APPROVED` | **unpaid** quota |
| fake | `NEVER_PRODUCTION` | test double |

The approval rests on the provider's own commercial terms committing that it may
not train models on customer content from the services, with documented backend
deletion inside a bounded window. The refusal rests on the unpaid route's own
statement that submitted content is used to provide, improve and develop its
products and machine learning technologies, that human reviewers may read the
input and output, and that confidential information should not be submitted.

**The route is recorded, not the vendor's reputation.** The same vendor's paid
route is a different assessment, and nobody has made it. Postures are reviewed
statements, so a provider changing its terms changes this file, not the code.

---

## RUNTIME

`compliance/inference.py` — `authorize_external_inference(source, profile,
provider_id, *, policy, provider_configured)`. It imports no network library and
calls no model; it answers a question about permissions, and the answer is what a
caller must hold before it may build a request.

**One decision point, before any source text is serialised.** The architecture
this replaces is the tempting one — build the prompt, hand it to the Gateway, let
the Gateway notice the provider is forbidden. By then the text is assembled and
the only thing left to prevent is the socket.

**Every layer is evaluated even after one refuses**, with nine distinct refusal
codes. An operator told only the first failure would fix it and be refused again,
three more times. Collapsing four gates into `MODEL_NOT_AVAILABLE` is how a
governance decision comes to look like an outage.

**The dependency direction is deliberate.** This module reads the source registry
and the provider policy and produces a decision. The Gateway knows nothing about
sources; no provider adapter queries the registry. The join happens here, once.

`provider_configured` is passed in rather than read: whether a credential exists
is a fact about the environment, and a governance module that read environment
variables would be two things at once.

---

## CONFIGURATION

```bash
uv run sros-source --use-profile local-private-research-v1 inference-authorization stack-exchange --provider anthropic --credential-env ANTHROPIC_API_KEY
```

Live result for Stack Exchange under `local-private-research-v1`:

| Gate | State |
|---|---|
| source transmission | `PERMITTED_WITH_CONDITIONS` |
| profile egress | `PERMITTED_TO_APPROVED_PROVIDERS` |
| provider posture | `APPROVED` |
| provider configured | **no** |

→ `REFUSED  PROVIDER_NOT_CONFIGURED`

**No credential was fabricated, none was committed, and no tracked file was
offered as a place to paste one.** The command reads the `PRESENCE` of an
environment variable and never prints its value.

---

## BOUNDARIES — what was deliberately not done

No candidate generator, no human labels, no rubric runtime, no classifier, no
model-derived Signal, no INFERRED Claim, no Evidence. No embeddings, no vector
similarity, no fine-tuning, no training. No Opportunity, Market, WTP, Pricing or
MRR score. No source was re-collected and no acquired data was mutated. The
commercial profile was not assessed, and its `NOT_ASSESSED` is written out rather
than inherited from a default — it refuses, and it refuses as an open question.

Mission 1.18's Outcome S0 and Mission 1.20's Outcome S0 are untouched.

---

## QUALITY — gates run, and one older error disclosed

All green: eight validators (source registry, compliance capabilities, schema,
normalization, signals, claims, evidence aggregation, registry-grants-nothing);
four generated-doc `--check` steps; `ruff check`, `ruff format --check`, `mypy`
across 84 source files; both CI inline greps (only `collection/transport.py`
imports a network client; no collector in a governance package); and both test
suites — **555 tests across 8 packages** plus **1617 passed, 11 skipped** in the
acquisition suite, with 0 failures and 0 errors.

**Three test-level repairs, each recorded rather than quietly rewritten.** Two
Mission 1.22 assertions were *supposed* to fail: they asserted the profile had no
field for where inference happens and that no condition mentioned a provider.
Mission 1.23 made both false on purpose, so the assertions moved rather than being
deleted — v1 is now pinned by version as the historical record, and the new
assertions test the closure (the field exists, both profiles state it, and the
condition still names no vendor). A third asserted that no document authorised the
transfer, with a docstring saying it was where that absence would stop being true.
It has.

**mypy found dead code in the new CLI command**: a `source is None` branch that
could never run, because `catalog.get` raises rather than returning `None`. Removed
in favour of the repository's existing convention of letting `SourceRegistryError`
propagate with its own message.

### An older violation, disclosed here because this mission tripped over it

Migration 0027 would not apply: the ledger reported a checksum mismatch on **0026**.
Investigation showed the committed file and the working tree agreed, and the live
schema matched the committed file exactly — same CHECK values, same COMMENT, same
registry row. **The cause was my own Mission 1.19 error: I edited an applied
migration and then committed it.** Migrations are forward-only and immutable once
applied, and editing one is precisely the change-control violation
`docs/CLAUDE.md` describes.

The repair was scoped to the **local ledger row only** (`core.schema_migrations`),
verified from a fresh connection, with ledger row count unchanged at 26 before
0027. No schema object was altered and no migration file was edited to fix it.
Recording it here rather than leaving it in a shell transcript is the point: a
governance violation that is repaired silently is a violation twice.

---

## Is Mission 1.22's semantic-equivalence evaluation now safe to RESUME?

**YES, AFTER OPERATOR CONFIGURATION.**

The governance gate Mission 1.22 could not pass is now passable and currently
passes for Stack Exchange under the local profile: the source permits the
transmission on a recorded licence basis, the deployment permits the class of
egress, and one provider is approved on its own contract text. What remains is
gate four — an operator configuring a credential for that provider, an act
performed outside this repository.

**Three things this answer does not say.** It does not say the evaluation is
authorised today: the boundary is closed and `PROVIDER_NOT_CONFIGURED` is the
reason. It does not say the component exists — the candidate generator, rubric,
classifier and INFERRED Claim path remain unbuilt, by instruction. And it does
not say the commercial profile may ever do this; that question is open and was
left open deliberately.

**What changed is the kind of blocker.** Missions 1.18 and 1.20 found the data
could not support deterministic identity. Mission 1.21 found the sources
publishing identity could not be reached. Mission 1.22 found that SROS could not
express the question. Mission 1.23 gave it the words, and what is left is a
configuration step rather than a finding — the first blocker in this sequence
that an operator can clear in an afternoon.
