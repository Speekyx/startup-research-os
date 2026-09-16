# Mission 1.85.3 report: first-person semantic extraction contract and evaluation preregistration (N08-A)

**Outcome: `CONTRACT_PREREGISTERED_HUMAN_LABELS_AND_EGRESS_REQUIRED`.**

SROS now has a versioned, testable answer to one question: what may a model infer from one authorised
first-person text record, how is that interpretation represented, and how will we prove the extractor is
good enough before using it.

**What exists:**
- the contract;
- a deterministic validator;
- a frozen 98-record evaluation corpus;
- two blank human-label packs;
- 17 adversarial fixtures.

**What does not exist:** no model has answered any Stack Overflow question, no provider execution is
approved, and no production semantic finding exists.

Started from `main` at `3f13288`. Five read-only agents: A (D-12 historian), B (ontology fit), C
(extraction architecture), D (evaluation design), E (egress and privacy). The main agent was the only
writer.

| counter | value |
|---|---|
| PROVIDER_CALLS, MODEL_INFERENCES, EMBEDDING_CALLS | 0 |
| NEW_EXTERNAL_DATA_REQUESTS, NEW_EXTERNAL_DATA_PERSISTED | 0 |
| PRODUCTION_MODEL_DERIVED_SIGNALS, PRODUCTION_CLAIMS, PRODUCTION_EVIDENCE | 0 |
| NEW_INDEPENDENCE_STATES, NEW_SCORES, HUMAN_LABELS_ENTERED | 0 |

Contract: `docs/data/first-person-semantic-extraction-contract-v1.md` and `.json`. Every one of the 17
required deliverables is a numbered section there. This report records the findings and the verification.

## 1. D-12, recovered rather than inferred

**What D-12 is.** D-12 is "embedding model versioning and re-embedding strategy":
- defined in `specification-audit.md:227` and `mission-0.1.1-decisions.md:63`;
- tied to `EMBEDDING_MODEL` at `ADR-006:216`;
- OPEN in every document since Mission 0.1, and never decided;
- **no conflict** with the selected route, which uses no embedding, vector, similarity or clustering.

**Scope drift, recorded and not edited.** Four texts cite D-12 as blocking classification in general:
- the `NLP_EXTRACTION` capability block in `plan.py`;
- `services/nlp/README.md`;
- a manifest sentence;
- the prompt registry.

That is broader than its definition. Re-grounding the block is an operator decision for N08-B, and no
capability was unblocked.

**Nine blockers, kept separate** (contract §1):
- embeddings;
- the profile's embeddings flag;
- the planner block;
- two import-placement guards;
- the Signal S-1 rule;
- the parked problem-family relation;
- the unauthorised exact-equivalence relation;
- human labels;
- the ADR-033 egress gates.

They block different things, and merging them into one rule would have hidden which decision unblocks
what.

## 2. Findings that shaped the design

1. **A per-record finding cannot be a Signal.**
   - Signal rule S-1 requires two distinct observations: `MINIMUM_DISTINCT_OBSERVATIONS = 2`, counted by `observation_key`. One question is one observation.
   - The Signal contract also calls one model call per observation a design error.
   - This is why the stop condition "the Signal contract cannot represent MODEL_DERIVED extraction" did **not** stop the mission. The per-record finding is designed as a non-canonical artifact that never claims to be a Signal. A Signal is a later deterministic count over at least two validated records, and it needs its own ADR (N08-C).
2. **`MODEL_DERIVED` exists and carries little.**
   - Its only requirement is `model_version`. There is no provider column, and Signal identity ignores the model.
   - The finding's identity therefore **includes** provider, model and prompt.
3. **Architecture B selected.** Model → verbatim quotes and closed-enum labels → a model-free validator that computes offsets against a surface recomputed from the held record → non-canonical extraction.
   - A was rejected: it breaks S-1.
   - C was rejected for the write path: a promoted candidate is still one observation, and a durable candidate store is ADR-038's "Claims before Claims".
4. **Two extractable labels.**
   - `REPORTED_FAILED_ATTEMPT` → `PROBLEM_OR_NEED`, `REPORTED_BEHAVIOUR`.
   - `NEGATIVE_EVALUATION_OF_NAMED_SOLUTION` → `SOLUTION_DISSATISFACTION`, `STATED_OPINION`.
   - Seven more are recorded as ANNOTATION_ONLY, BLOCKED or NOT_SAFE, each with its blocker.
   - `PROBLEM_STATEMENT` was excluded because it is near-constant on this site.
   - Hypothetical willingness to pay is BLOCKED: `WILLINGNESS_TO_PAY` means paid or committed, and mapping a hypothetical there would license the "would pay" sentence the opportunity guard unlocks.
5. **The body is HTML.** Verified on the held records. So the text surface is itself versioned: `se-question-text-surface@1.0.0`.
   - `<pre>` code is kept byte for byte in `[CODE]` regions, and blockquotes go in `[QUOTE]` regions.
   - That is how the validator refuses quoted complaints outright, and evaluation labels whose span sits inside error text.
6. **Egress separates cleanly** into three independent permissions:
   - **Source:** Stack Exchange local review v2 permits transmission with conditions.
   - **Provider:** the Anthropic API-key route is APPROVED on documents from 2026-09-02, and must be requalified at run time.
   - **Operator:** a packet-scoped approval, which does not exist yet.

## 3. The held corpus, proven

| fact | value |
|---|---|
| resource | `stack-exchange` / `questions/stackoverflow`, `community_question`, `local-private-research-v1` |
| held normalized records | 104, all `VALID`, none superseded, 104 distinct question ids, no null body |
| acquisitions | docker over March 2024 (89); python on 2024-03-04, pages of 10 and 5 |
| stored fields | `question_id, site, title, body, tags, creation_label, answer_count, is_answered, accepted_answer_id, score, view_count, question_url, content_licence` |
| excluded at acquisition | `owner` and all sub-fields, `last_editor`, `comments`, natural-person names, personal identifiers; `author` null |
| licence and attribution | CC BY-SA 4.0 per item; Stack Exchange Network, licence identifier, item link |
| model processing | `model_processing` PERMITTED_WITH_CONDITIONS; `external_model_transmission` PERMITTED_WITH_CONDITIONS (review v2: provider no-training, bounded retention, inference only) |
| included in the corpus | 98 (DEVELOPMENT 50, HOLDOUT 48; docker cohort 85, python cohort 13) |
| excluded | 6, per-item content licence not reported by the source |
| residual identifier patterns | URL in 40 records, IPv4-like 19, long token 7, user home path 5, handle 4, email-like 2 (counts only) |
| expiry | raw records from 2026-10-01; normalized records from 2027-09-01 |

Approval for Stack Overflow questions was not generalised to answers, comments, users, other sites or other
sources.

The records were normalized under review v1. Review v2 added the transmission assessment, and a future run
must verify its conditions.

## 4. Deliverables

1. D-12 decision map: contract §1 and JSON `d12_decision_map`.
2. Architecture comparison: §2.
3. Selected architecture: §3.
4. Extraction schema and contract: §4, and `sros_semantic_extraction_contract.finding`.
5. Label definitions: §5–§6, and `labels.py`.
6. Per-label ontology mapping: §7, checked by `test_semantic_extraction_ontology_fit.py`.
7. Prohibited inferences: §8.
8. Persistence and promotion boundary: §9. The minimal staging schema is specified, not created.
9. Source-lineage rules: §10.
10. Independence inheritance rules for N06: §11.
11. Prompt-injection boundary: §12, and 17 synthetic fixtures.
12. Evaluation protocol: §13.
13. Proposed thresholds, all `PROPOSED_NOT_AUTHORISED`: §14.
14. Frozen corpus manifest: `stack-overflow-semantic-evaluation-corpus-v1.json`.
15. Blank human-label packs: `stack-overflow-semantic-label-pack-{development,holdout}-v1.json`. Every cell is `UNLABELLED`, origin and annotator are null, `AI_ASSISTED_PROVISIONAL` is not allowed, and no text is inlined.
16. Future egress requirements: §16.
17. N08-B and N08-C plan: §17.

## 5. Verification

- **No model, provider or embedding call.** The new package imports only the standard library and `sros-contracts`, asserted over its syntax tree. The corpus builder reads the local database in a `READ ONLY` transaction and imports no model or network client.
- **No new external data.** Every record comes from the canonical tables; nothing was fetched.
- **Canonical counters unchanged**, before and after: raw 325, normalized 325, signals 60, claims 91, claim revisions 92, evidence 112, reliability assessments 4, independence groups 0, opportunities 1, hypothesis revisions 2, hypothesis evidence 14, embeddings 0, source policy reviews 71, scores absent.
- **Held Stack Exchange records unchanged.** `--check` re-reads them and reproduces the frozen manifest and packs byte for byte.
- **Historical reviews unchanged.** No diff to the source catalog, compliance or provider policy.
- **N05 unchanged.** Predecessor sha256 is `8e69aef5...`; sensitivity `--check` passes; the replay gives 91/91 identical claims.
- **Guards pass.** `validate_signals` (7 groups) and `validate_claims` (11 groups).
- **Human-label fields are blank**, asserted per cell.
- **Every label maps to an existing member or names its blocker**, asserted against `EvidenceDimension` and `EvidenceObservationCategory`.
- **Tests.**
  - Contract package: 31 tests (surface, validator, fixtures, package boundary, contract and code agreement, split recomputation, blank packs).
  - Opportunity engine: 5 ontology and roadmap tests.
  - Roadmap and qualification: 82 still passing.
  - Bare runner: 3,926 tests across 10 packages.
  - `ruff check`, `ruff format --check` and `mypy` on the new package are clean.
- **Probes.** No semantic-generation mutation probe was run; no Mission 1.84 file was touched.

## 6. Roadmap

| node | status |
|---|---|
| N08 | `CONTRACT_PREREGISTERED_HUMAN_LABELS_AND_EGRESS_REQUIRED` (mission 1.85.3), not DONE |
| N05 | DONE, algorithm 1.1.0 unchanged |
| N01 | `NO_GO_OPERATOR_DECISION_REQUIRED` |
| N02 | unbound |
| N06 | not started |

## 7. What remains and who decides

**Human labels.**
- Two or more annotators on the development pack.
- The composition and agreement verdicts decide whether each label can become gold.
- `NEGATIVE_EVALUATION_OF_NAMED_SOLUTION` is likely to be `EVALUATION_INSUFFICIENT` on a 48-record holdout. That is preregistered; the response is not a lowered threshold.

**Operator decisions.**
- Accept or revise the proposed thresholds.
- Re-ground or keep the `NLP_EXTRACTION` / D-12 wording.
- Residual-identifier policy (exclude or review, rather than redact).
- Provider requalification and a packet-scoped egress approval.

**Engineering, N08-B and N08-C.**
- The prompt and strict-tool extractor package.
- Staging tables only after a PASS.
- An ADR for a count Signal and the INFERRED claim path.
- The independence invariants in N06.

**Debt recorded.**
- The expiry of the raw records (2026-10-01) does not affect the corpus, which references normalized records. Labelling should still finish before normalized expiry.
- Whether provider error bodies can echo prompts into logs is unverified.
- Surface markers are line-based, so a code line printing `[/CODE]` exactly would close a region early. The validator treats that conservatively.

Mission 1.85.4 was not started.
