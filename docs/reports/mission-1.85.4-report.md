# Mission 1.85.4 report: human reference and evaluation execution readiness (N08-B)

**Outcome: `EVALUATION_TOOLING_READY_HUMAN_LABELS_AND_EGRESS_REVIEW_PENDING`.**

Everything a bounded model evaluation needs now exists offline:
- the corrected D-12 scope;
- the human annotation, import, agreement and adjudication tooling;
- the residual-identifier scan and egress eligibility;
- a documentation-only provider requalification;
- a versioned prompt, a forced strict tool, and an offline extractor integrated with the contract validator;
- a threshold decision package;
- a frozen development packet.

The packet is `BLOCKED_HUMAN_LABELS` and cannot receive an approval. The final state is therefore not
`READY_FOR_PACKET_SCOPED_OPERATOR_APPROVAL`. It is a precise list of blockers (§11).

Start: `main` at `d0c4064`. Five read-only agents:
- A: D-12 and `NLP_EXTRACTION`;
- B: annotation and adjudication;
- C: residual identifiers and the no-redaction invariant;
- D: provider requalification;
- E: governance and provider reachability.

The main agent was the only writer.

| counter | value |
|---|---|
| PROVIDER_CALLS, MODEL_INFERENCES, EMBEDDING_CALLS | 0 |
| STACK_OVERFLOW_TEXT_EGRESS, NEW_EXTERNAL_RESEARCH_DATA | 0 |
| PRODUCTION_SEMANTIC_FINDINGS, SIGNALS, CLAIMS, EVIDENCE | 0 |
| NEW_INDEPENDENCE_STATES, NEW_SCORES | 0 |
| HUMAN LABELS ENTERED (by anyone) | 0 |

Documentation retrieval was authorised, and 16 provider documentation pages were retrieved. No inference
endpoint was called.

## 1. D-12 and NLP_EXTRACTION, re-grounded

**D-12 is embedding-model versioning and the re-embedding strategy.** It is still OPEN and was not closed.

**Code.**
- The planner's `NLP_EXTRACTION` block cited D-12 for "classification, embedding and clustering". It now cites `N08-SEMANTIC-EXTRACTION-GATE`: human reference labels, threshold authorisation, a packet-scoped operator approval, the ADR-033 egress gates and the contract validator.
- D-12 stays on `OPPORTUNITY_DISCOVERY`, which clusters, with the reason rewritten to say so.
- `PLANNER_VERSION` moves from 1.4.0 to 1.5.0, a blocking-set change with the graph unchanged.
- No capability was unblocked, embeddings stay disabled, and nothing was revived: no similarity, clustering or problem-family relation.

**Corrected current statements.** The planner code and its enum comment, the orchestrator package docstring
and README, `services/nlp/README.md`, the prompt registry docstring, one current invariant in `docs/CLAUDE.md`,
and two current sentences in `PROJECT_MANIFEST.md`.

**Left alone.** Historical mission reports, ADRs, version rows and changelog entries.

**Tests.**
- `test_nlp_extraction_is_gated_by_n08_and_not_by_d12`;
- `test_d12_remains_open_and_governs_clustering`;
- `test_d12_remains_open_as_recorded`, which checks the specification-audit row.

## 2. Annotation workflow

`docs/data/stack-overflow-semantic-annotation-workflow-v1.md` and `infrastructure/scripts/semantic_annotation.py`.

**prepare.**
- Writes a working copy **outside the repository**: the blank development pack, a deterministic per-annotator record order, an unfilled attestation, and the rendered surfaces.
- Refuses a folder inside the repository, a non-human origin, and holdout.

**lint and import.** These validate with `annotation.validate_annotation_pack`. Every check runs and any refusal rejects the pack. It refuses:
- a missing or non-human origin (`AI_ASSISTED_PROVISIONAL` refused);
- a placeholder or model-like annotator id;
- an incomplete attestation or a model field;
- a record-set or shuffle-order mismatch;
- an `UNLABELLED` cell or a surface digest mismatch;
- a quote not in the surface, or in quoted or code regions where the label forbids it;
- `PRESENT` without a span, a span on a non-`PRESENT` cell, a missing or forbidden subject, `UNCERTAIN` without a note, and incidence labels carrying spans;
- any holdout path, split or record, raised as `HoldoutAccessError` before anything else.

Evidence is entered as quote plus occurrence, exactly as the model does, and the tool computes the offsets.

**What is committed:** states, offsets and digests only. Quotes and notes stay local.

**Limit, stated wherever labels are reported:** the tooling cannot prove a human typed the labels. That rests
on the attestation and the operator's statement.

**Fix to Mission 1.85.3:** `--render-working-copy` wrote development and holdout surfaces into one folder. It
now requires `--split DEVELOPMENT`.

## 3. Adjudication and composition

`sros_semantic_extraction_contract.agreement`.

**Composition metrics** (no model assistance, no threshold chosen in code):
- per-label state counts and prevalence;
- Cohen's κ, both three-state and PRESENT/ABSENT;
- Krippendorff's α;
- raw agreement, positive-specific and negative-specific agreement, prevalence and bias indices, and PABAK;
- span agreement: exact, overlap and character Jaccard;
- subject agreement for the negative-evaluation label.

**Gates.** The composition gate and κ floor are read from the contract with their status, and reported as
`GATE_NOT_AUTHORISED` while `PROPOSED_NOT_AUTHORISED`.

**Adjudication queue.** A pair is queued when:
- the states differ;
- any annotator marked `UNCERTAIN`;
- both marked PRESENT but the spans do not overlap;
- both marked PRESENT on the negative-evaluation label but the subjects do not overlap.

**Adjudication file validation.**
- The method is a third human (not an annotator) or a recorded joint session.
- The origin is human and `model_output_consulted` is literally false.
- The queue digest matches, and the items cover exactly the queue.
- Resolutions are an existing state, a reread with a note, or unresolved-kept-`UNCERTAIN`.

The reference is recomputed as agreed cells plus adjudicated items, and never stored.

**Sub-gate: `HUMAN_LABELS_PENDING`.** No real human labels exist, and `analyse` says so and writes nothing.

## 4. Residual-identifier scan and egress eligibility

**Policy: `REVIEW_OR_EXCLUDE_NO_REDACTION`.** The module is `sros_semantic_extraction_contract.egress`, driven
by `infrastructure/scripts/build_semantic_egress_eligibility.py`.

**The scan.**
- It runs on the **exact transmitted surface**. Agent C showed the Mission 1.85.3 counts were taken on title plus unescaped HTML, which is different text, so they were not reused.
- Version `residual-identifier-scan@1.0.0`, with a pinned pattern-table digest.
- Patterns: URL, URL with userinfo, email-like, IPv4-like, IPv6-like, user-home path, handle, long token, and secret-like.
- It is a review trigger only. Counts are committed; offsets and matched text go only to a local review folder outside the repository.

**Eligibility, derived and never stored by hand.**
- A mechanical rule may only **exclude**: a surface containing a transport delimiter (`<<<`, `>>>`, or the neutralisation marker) would be rewritten by the Gateway, so the transmitted bytes would differ from the surface.
- Otherwise, only a `HUMAN_OPERATOR` decision bound to the surface digest approves or excludes.
- Otherwise the record is `EGRESS_REVIEW_REQUIRED`.
- A bulk decision may only accept listed zero-trigger records. `REVIEW_REQUIRED` is never recorded, a non-human origin is refused, and there is no redaction function (asserted over the package's syntax tree).

**DEVELOPMENT, 50 records.**
- 22 records carry at least one trigger: url 12, ipv4 8, long token 4, secret-like 3, home path 3, handle 3, email 1, url-with-userinfo 1.
- 1 record is `EGRESS_EXCLUDED` (transport delimiter).
- 49 records are `EGRESS_REVIEW_REQUIRED`.
- 0 records are `EGRESS_APPROVED`.
- The decision file is committed blank.

Holdout was not scanned.

## 5. Provider requalification

`docs/data/anthropic-api-route-requalification-v1.json`, a **successor** review. `model-provider-policy-v1.json`
was not edited, and its digest is bound.

**How the evidence was gathered.**
- 10 first-party pages were retrieved as raw bytes, each with a full sha256.
- Every decisive quote was re-read verbatim from those bytes by the main agent. One ZDR sentence did not match and is not quoted.
- Page bytes are not committed.

**Findings.**
- **Training.** No training on Customer Content under the Commercial Terms, and commercial API inputs and outputs are not used by default. Unchanged.
- **Retention.** Backend deletion within 30 days, **except** longer-retention services, a separate agreement, Usage Policy enforcement and legal compliance. The 2026-09-02 record quoted the sentence without its exceptions.
- **Trust and safety.** Flagged content is kept up to 2 years (classifier scores up to 7), even under ZDR. Not recorded before.
- **ZDR.** It exists per organisation. Whether the operator's organisation has it is NOT_ESTABLISHED.
- **Covered Models.** Fable 5.1, Mythos 5.1, Fable 5 and Mythos 5 require 30-day retention. `claude-sonnet-5` is not a Covered Model and is active.
- **Strict tools.** Prompts and outputs are not stored; the JSON schema is cached up to 24 hours.
- **Errors.** JSON with a type and message. **Whether an error can echo submitted content, and any other diagnostic logging, are NOT_ESTABLISHED.** Silence is not permission, so the runner never stores error bodies or exception text.
- **Region and consumer route.** Regional controls do not change retention. The consumer subscription route remains a separate route, NOT_APPROVED.

**Verdict: `REQUALIFIED_WITH_CONDITIONS`.** The source conditions hold: no training, and bounded retention
with its exceptions bound in the packet rather than assumed away.

## 6. Prompt, strict tool and offline extractor

New package `packages/semantic-extraction` (`sros_semantic_extraction`, depending only on the contracts, the
Gateway types and the contract package).

**Prompt: `first-person-semantic-extraction-prompt@1.0.0`.**
- The trusted system and task regions hold the task.
- One untrusted region carries the **surface byte for byte**, labelled `packet-record-<index>`. A test checks this on all 17 fixtures.
- In-source instructions have zero authority, stated in the system region.
- No chain-of-thought, confidence, rationale or offsets.
- Verbatim quotes are required, and a verbatim subject for the negative-evaluation label.
- Withheld: score, views, answer count, accepted state, tags, URL, author, record id. Canary tests confirm none reaches the body.
- A surface with a transport delimiter is refused before any prompt exists.

**Tool: `first-person-semantic-extraction-tool@1.0.0`.**
- One forced strict tool. The strict schema is exactly the reviewed projection of the canonical schema, with no local-only keywords sent.
- Thinking disabled, `max_retries=0`, no other tools, no fallback provider.

**Retry reading, within N08-A.**
- A schema failure (no payload, missing keys, or an incomplete forced tool call) may be retried at most once.
- A validator refusal and a provider error are never retried.
- This reading is recorded as needing operator ratification.

**Package boundary, enforced over the syntax tree.** The package imports no provider, transport, gateway
executor, acquisition or NLP module, contains no `.complete(`, `post_json`, `environ` or `getenv`, and cannot
reach a provider.

## 7. Evaluation packet and approval boundary

`docs/data/semantic-extraction-evaluation-packet-development-v1.json`, rendered from committed artifacts,
checked in CI.
- **Digest:** `1ed9faf8b3807599fc346a125f2a9c64912874a5b79408357fae55db498d386b`
- **Status:** `BLOCKED_HUMAN_LABELS`

**What the packet binds.**
- **Versions and digests:** contract, surface, label set, validator, prompt, tool schemas (strict and canonical), requalification, provider policy, catalog, corpus and eligibility.
- **Provider and model:** anthropic, `claude-sonnet-5`, `max_tokens` 4096, thinking disabled, excluded features listed, no fallback.
- **Selection:** development records only, with holdout excluded, and the exact approved, excluded and review-required subsets.
- **Execution:**
  - retry policy, and a 240-second timeout;
  - `max_calls` = approved records × 2, currently 0, with input and output token bounds;
  - planning estimate of $0 now, and $2.71 if all 49 reviewable records were approved (an estimate only);
  - hard ceiling bound to the approved set: $0 now, about $220 for 49 records, based on the 1M-token context window, because tokens per character are not established.
- **Logging policy:** status, error class, request-id and digests only.
- **Expected outputs:** local, outside the repository, with zero canonical writes.

**The runner (`run_semantic_extraction_evaluation.py`)** is dry by default and builds no transport. Under
`--execute` it refuses before any transport exists:
1. a digest that does not match the pinned value;
2. an approval flag written into the packet;
3. **any status other than `READY_FOR_PACKET_SCOPED_OPERATOR_APPROVAL`, before it reads an approval**;
4. an approval-file digest that differs from `--approval-sha256`;
5. an approval that does not name this packet or accept the ceiling, the retention bound and the retry reading;
6. an existing attempt record;
7. a failed ADR-033 authorisation.

After those checks it writes `ATTEMPT_STARTED` exclusively before the first request, and has one call site.
The real transport appears only in `main`.

Tests cover every refusal, the approval matrix, write-ahead spending, bounded calls, the retry behaviour with a
fake gateway, and that a provider error echoing text leaves no text in the outputs. No approval or attempt file
exists. **Merging authorises nothing.**

## 8. Threshold decision package

`docs/data/semantic-extraction-threshold-decision-package-v1.json`. It covers 11 items, every one
`PROPOSED_NOT_AUTHORISED`. Each item states:
- its rationale;
- the false-positive and false-negative risk;
- the required support;
- whether development can estimate it and whether the 48-record holdout can test it;
- what produces PASS, FAIL and `EVALUATION_INSUFFICIENT`.

The overall outcome rule is fixed before results.

Candidly, a 0.10 false-positive bound for the negative-evaluation label needs about 30 PRESENT predictions,
which the holdout is unlikely to contain. The preregistered answer is `EVALUATION_INSUFFICIENT`, never a lower
bar.

## 9. Holdout isolation

- The holdout pack's sha256 is pinned and unchanged.
- It is not rendered, prepared, scanned, packeted or analysed.
- Every development path refuses it.
- No holdout annotation or adjudication file exists.

## 10. Verification

- **Zero provider calls and zero Stack Overflow egress.** The extractor package has no call site, network import or credential read. The only call site is in the runner, which refuses the blocked packet, and no approval or attempt exists. Documentation retrieval touched only public documentation pages.
- **Corpus unchanged.** The corpus, packs and held records are unchanged: `build_semantic_evaluation_corpus.py --check` passes, and the packs and manifest are pinned by digest.
- **Canonical counters unchanged** before and after: raw 325, normalized 325, signals 60, claims 91, revisions 92, evidence 112, reliability assessments 4, independence groups 0, opportunities 1, hypothesis revisions 2, hypothesis evidence 14, embeddings 0, source policy reviews 71, scores absent.
- **No AI-written labels.** No annotation file exists, the blank packs keep their digests, and no module assigns a label state (checked over the syntax tree).
- **D-12 OPEN, embeddings disabled.** The profile flags and the embedding guards are untouched.
- **N05 unchanged.** The predecessor digest matches, the sensitivity check passes, and the replay gives 91/91 identical.
- **No source verdict reopened.** The source catalog and provider policy are byte-identical.
- **Tests and checks.**
  - Contract package: 50 tests.
  - Extractor and runner: 23.
  - Orchestrator: 97.
  - Roadmap, qualification and ontology: 87.
  - Gateway: 171.
  - Bare runner: 3,947 tests across 10 packages.
  - `ruff check`, `ruff format --check` and `mypy` are clean.
  - The packet, egress and corpus `--check` commands all pass.

## 11. What remains before a model evaluation

1. **Human labels.** At least two human annotators on the development pack, then import and analysis.
2. **Adjudication** of the queue by a third human or a recorded joint session.
3. **Egress review.** A human operator decides the 49 review-required development records.
4. **Threshold decision.** The operator authorises or revises each item before any holdout result.
5. **Retry ratification.** The operator ratifies the schema-failure retry reading, or narrows it.
6. **Cost ceiling.** The operator accepts the hard ceiling, or authorises a smaller documented input bound. The price must be re-verified at approval.
7. **Re-render and approve.** Re-render the packet until its status is `READY_FOR_PACKET_SCOPED_OPERATOR_APPROVAL`, then a separate operator approval naming its final digest.

Also recorded:
- the error-echo and diagnostic-logging questions stay NOT_ESTABLISHED and are contained by the logging policy;
- the requalification must be refreshed if a run falls outside its 180-day window;
- the normalized records expire from 2027-09-01.

Mission 1.85.5 was not started.
