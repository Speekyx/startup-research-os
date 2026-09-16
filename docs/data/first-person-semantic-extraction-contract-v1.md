# First-person semantic extraction contract v1 (roadmap N08-A)

**Status: `CONTRACT_PREREGISTERED_HUMAN_LABELS_AND_EGRESS_REQUIRED`.** Mission 1.85.3, 2026-09-16.

This contract answers one question: *what may a model infer from ONE authorised first-person text record, how
is that interpretation represented, and how will we prove the extractor is good enough before using it?*

It is a design and a preregistration.
- No model has read any record.
- No provider execution is approved.
- No finding exists, and nothing was persisted.

Machine-readable form: [`first-person-semantic-extraction-contract-v1.json`](first-person-semantic-extraction-contract-v1.json).
Code: `packages/semantic-extraction-contract` (standard library plus `sros-contracts`; no prompt, no model, no
network, no persistence).

**The model is an interpreter, not a source.** A finding states a bounded interpretation of text already
held. It never becomes the source observation, and the two stay separately addressable.

## 1. Recovered D-12 decision map

**D-12 is "Embedding model versioning and re-embedding strategy".**
- It is defined in `specification-audit.md:227` and `mission-0.1.1-decisions.md:63`, and tied to `EMBEDDING_MODEL` at `ADR-006:216`.
- It has been **OPEN in every document since Mission 0.1 and was never decided.**
- **It does not conflict with this contract**, which uses no embedding, vector, similarity or clustering.

**Scope drift, recorded, not edited.**
- Several texts cite D-12 as blocking classification in general:
  - the `NLP_EXTRACTION` capability block in `plan.py:168-183`;
  - `services/nlp/README.md`;
  - a manifest sentence;
  - the prompt registry.
- That is broader than the recorded definition.
- Whether to re-ground the block is an operator decision for N08-B. This mission unblocks no capability.

**The separate blockers.** They are different in kind and are not merged into one rule.

| id | blocker | blocks | status |
|---|---|---|---|
| B1 | D-12 | embeddings, vectors, similarity, clustering | OPEN |
| B1b | profile `embeddings: false` | embeddings, independently of D-12 | in force |
| B2 | `NLP_EXTRACTION` block citing D-12 | the planner's NLP stage | in force, wording broader than D-12 |
| B3 | `validate_signals.py` Gateway import ban | model code in the signal layer (a placement rule) | frozen |
| B4 | `validate_claims.py` OBSERVED-only guard | non-OBSERVED claims in the interpreters | frozen |
| B5 | Signal S-1 (two distinct observations), numeric magnitude, closed quantity family, no model call per observation | a per-record finding being a Signal | frozen |
| B6 | `SAME_PROBLEM_FAMILY` PARKED | cross-record problem identity, recurrence counts | parked, not revived |
| B7 | EXACT equivalence established nothing | equivalence as Signal/Claim/Evidence | not authorised |
| B8 | human reference labels | *validated*, *gold*, production inference | open |
| B9 | ADR-033 four gates | sending text to an external model | source, profile and provider gates permit; no packet-scoped operator approval |

**Frozen** (changed only by a new version or an ADR):
- S-1;
- the MODEL_DERIVED provenance checks;
- the model is never the evidence, and no chain-of-thought is stored;
- both import guards;
- the four gates;
- UNKNOWN is never promoted;
- reliability is per scope;
- the verdicts of Missions 1.24, 1.25 and 1.27;
- N05 algorithm 1.1.0.

**Open:**
- D-12 itself;
- the scope of the `NLP_EXTRACTION` block;
- the staging schema;
- a count Signal over findings;
- the INFERRED claim path;
- human labels;
- threshold acceptance;
- packet-scoped egress approval.

## 2. Architecture comparison

| | A. model → Signal | **B. model → validated observation → deterministic builder** | C. model → candidate → human promotion → Signal |
|---|---|---|---|
| Signal S-1 | broken: one record is one observation | respected: finding is not a Signal | still one observation after promotion |
| provenance | model version only | full per finding | full, plus promoter |
| hallucination surface | high | quotes must exist verbatim; closed enums | low, but rubber-stamping risk |
| exact citation | lineage only | offsets computed by the validator | as B |
| uncertainty | squeezed into a number | explicit states, no number | as B |
| several findings per text | several one-record "Signals" | a finding list | as B |
| idempotency | Signal id ignores the model | identity includes model and prompt | adds promotion state |
| Claim/Evidence | model output one step from Evidence | model stays provenance | a durable pre-Claim entity (ADR-038's "Claims before Claims") |
| independence | reads as several witnesses | one witness per record | as B |
| verdict | REJECTED | **SELECTED** | REJECTED for the write path |

## 3. Selected architecture

```
held NormalizedRecord
  -> text surface se-question-text-surface@1.0.0 (deterministic)
  -> [N08-B: four gates, prompt regions, one forced strict tool]
  -> model payload: states, label ids, verbatim quotes, occurrence indices
  -> deterministic validator (this package)
  -> validated extraction: non-canonical, MODEL_DERIVED, is_signal = false, one witness
  -> [N08-C: deterministic count builder over >= 2 distinct records]
```

**What the model does:**
- It writes nothing.
- It never supplies offsets; the validator finds each quote in the surface it recomputed from the held record.
- It never supplies a rationale, a confidence number or a `does_not_establish` sentence.

**Package layout.** The future extractor, `packages/semantic-extraction`:
- depends on this contract and the Gateway only;
- never depends on `sros-acquisition` or `sros-nlp`;
- is itself added to `sros_nlp`'s import ban.

## 4. Extraction schema

**Model payload.** It is a closed object: `extraction_state` and `findings`.

`extraction_state` is one of:
- `FINDINGS_PRESENT`;
- `NO_FINDING_ESTABLISHED`;
- `ABSTAINED_TEXT_INSUFFICIENT`.

`findings` holds at most 8 items. Each item is exactly:
- `finding_type`: an EXTRACTABLE label;
- `evidence_quote`: 8 to 400 characters, verbatim, no surface markers;
- `evidence_occurrence`: which occurrence of the quote, starting at 1;
- `subject_quote` and `subject_occurrence`: 2 to 120 characters, verbatim, or both null.

**Validated extraction.**
- **Lineage:** `workspace_id`, `normalized_record_id`, `observation_key`, `source_id`.
- **Provenance:** contract, label set, surface and its sha256, extractor, prompt, provider, model, visible length.
- **`extraction_id`:** sha256 over lineage and provenance. The model and prompt are included; outputs are excluded, so a different answer under the same identity shows up as drift.
- **Each finding carries:**
  - `finding_id`: sha256 over the extraction, type and spans;
  - the computed evidence span and the subject span;
  - the ontology dimension and category;
  - the label's `does_not_establish` constant.
- **Fixed fields:** `derivation_kind = MODEL_DERIVED` (the repository's existing term), `is_signal = false`, `independent_witness_count = 1`.

**Refusals.** There are 18 reason codes, all listed in the JSON.
- Every check runs, and any refusal rejects the whole extraction.
- A refusal is never an abstention and never a zero-finding answer.
- A schema failure is treated as possible injection. It is retried at most once and never falls back to another provider.

**The text surface.**
- It is the unescaped title, a blank line, then the rendered body.
- `<pre>` blocks are kept byte for byte between `[CODE]` lines.
- Blockquotes sit between `[QUOTE]` lines.
- Line endings are LF; offsets are code points.

That is how the validator knows:
- a quote from someone else sits in a `[QUOTE]` region, and is refused;
- an emotional word in an error log sits in a `[CODE]` region, and is refused for an evaluation label.

## 5. Label definitions

Two labels are EXTRACTABLE. The other seven are recorded so that their absence is a decision.

| label | status | ontology fit | dimension / category |
|---|---|---|---|
| `REPORTED_FAILED_ATTEMPT` | EXTRACTABLE | SUPPORTED_BY_EXISTING_ONTOLOGY | `PROBLEM_OR_NEED` / `REPORTED_BEHAVIOUR` |
| `NEGATIVE_EVALUATION_OF_NAMED_SOLUTION` | EXTRACTABLE | SUPPORTED_BY_EXISTING_ONTOLOGY | `SOLUTION_DISSATISFACTION` / `STATED_OPINION` |
| `SUCCESSFUL_WORKAROUND` | ANNOTATION_ONLY | REQUIRES_SCOPE_DECISION | none |
| `EXPLICIT_FEATURE_REQUEST` | ANNOTATION_ONLY | SUPPORTED_BY_EXISTING_ONTOLOGY | incidence measured first ("is there a way to" is the ordinary question form) |
| `REPEATED_DIFFICULTY_SAME_AUTHOR` | BLOCKED | REQUIRES_SCOPE_DECISION | `RECURRENCE_OR_FREQUENCY` is cross-observation |
| `SWITCHING_INTENT` | BLOCKED | REQUIRES_TAXONOMY_EXTENSION | no dimension asks about switching |
| `STATED_HYPOTHETICAL_PAYMENT` | BLOCKED | REQUIRES_TAXONOMY_EXTENSION | `WILLINGNESS_TO_PAY` means paid or committed |
| `STATED_PAST_PAYMENT` | BLOCKED | REQUIRES_SCOPE_DECISION | unidentified self-report; G7 |
| `UNMET_NEED_AS_SOLUTION_GAP` | NOT_SAFE | NOT_SAFE_TO_REPRESENT | absence of evidence is not evidence of absence |

**`REPORTED_FAILED_ATTEMPT`.**
- **Is:** the asker states, in their own words, that they tried a specific approach and it did not work (an error, a wrong result, or no effect). A failed workaround is this label.
- **Is not:** a question that only asks how to do something.
- **Evidence** may lie in code, because error output is usually there.

**`NEGATIVE_EVALUATION_OF_NAMED_SOLUTION`.**
- **Is:** the asker states a negative evaluation of a solution named in the text (a tool, library, service or product).
- **Location:** outside code and quoted material.
- **Is not:** merely an error, or a question about why a tool behaves as it does.
- **Subject:** the named solution is required, as a verbatim string, not a canonical subject (G7).

**`PROBLEM_STATEMENT` was considered and excluded.** On Stack Overflow every question states being stuck by
site design, and `community_question_volume` already reaches `PROBLEM_OR_NEED` deterministically.

## 6. Label definitions and annotation rules

**States and spans.**
- Each cell is `UNLABELLED` (blank), `PRESENT`, `ABSENT` or `UNCERTAIN`.
- **Extractable labels:** `PRESENT` requires at least one verbatim evidence span. `NEGATIVE_EVALUATION_OF_NAMED_SOLUTION` also requires a verbatim subject. `UNCERTAIN` requires a note.
- **Incidence labels** (ANNOTATION_ONLY and BLOCKED) take a state only, with no span.

**Holder rule.** Only the asker's own first-person statements count. Quoted, attributed, negated or
hypothetical text is `ABSENT`. When sarcasm or rhetoric is unclear, use `UNCERTAIN`.

**Multi-label.** Labels are independent, and no label implies another. A failed attempt does not imply
dissatisfaction.

**Worked examples.** They must be written as abstract shapes and never quote a corpus record.

## 7. Per-label ontology mapping

Every dimension and category named above is an existing member. `test_semantic_extraction_ontology_fit.py`
checks this against `EvidenceDimension` and `EvidenceObservationCategory`.

No label can reach:
- `WILLINGNESS_TO_PAY`, `SOLUTION_GAP` or `MARKET_ACTIVITY`;
- the `MARKET_ACTIVITY` or `DIRECT_VALIDATION` categories.

No signal type was registered. Mapping a finding into a Signal is N08-C work.

## 8. Prohibited inferences

| from | never |
|---|---|
| asking a question | market demand |
| popularity, score, view count | importance, market size, willingness to pay |
| a tag | a product category or a finding's subject |
| an accepted answer | an objectively solved problem |
| one asker's statement | population frequency |
| a hypothetical purchase | actual spend |
| model confidence or agreement | evidence reliability |
| two findings from one record, re-runs, different models | independent evidence |
| two differently worded questions | the same problem |
| emotional words in error text | a negative evaluation |
| text inside a quote, a pasted issue, or code | the asker's own statement |

## 9. Persistence and promotion boundary

**In N08-A, nothing is persisted.** The validator returns an in-memory object.

**Stage 1: non-canonical artifact.** A minimal later schema is specified but not created:
- `nlp.semantic_record_extractions`: one row per extraction identity, with a state CHECK, provenance NOT NULL, and row-level security;
- `nlp.semantic_findings`: spans with a CHECK, and a parent state of `FINDINGS_PRESENT`;
- no foreign key from `research.claims` or `scoring.evidence`;
- the writer lives outside `sros_nlp`.

**Stage 2: Signal.** A Signal comes only from a deterministic builder over validated findings from at least
two distinct `observation_key`s. It needs an ADR covering:
- the quantity family (`COMMUNITY_QUESTION_VOLUME` is scoped to a site's own tags);
- a truthful `derivation_confidence` for MODEL_DERIVED;
- a provider column.

**Human promotion.** It is not in the write path for the two extractable labels. Human judgement is used
for reference labels and adjudication. A BLOCKED label that is later unblocked must say whether it needs
promotion.

## 10. Source-lineage rules

- Every finding carries one held record's `normalized_record_id` and `observation_key`.
- The surface is recomputed from the held record, and its digest must equal the digest the prompt was built from.
- A finding cites the surface, never a tag, score, view count or answer metadata.
- The NormalizedRecord is never modified. Observation and interpretation stay separately addressable.
- Attribution travels with any displayed derived artifact: Stack Exchange Network, CC BY-SA 4.0, and the item link.

## 11. Independence inheritance rules (for N06)

- All findings from one record inherit that record's single observation lineage: one witness.
- Several findings from one question are not independent evidence.
- Model re-runs are not independent evidence.
- Different models interpreting the same question are not independent evidence.
- One prompt and model across many records is a shared interpretive cause. It is recorded, never assumed away.
- Extraction writes no independence state.

## 12. Prompt-injection boundary

**Source text is untrusted data.**
- The four ADR-033 gates are resolved before any string containing question text exists.
- Each surface goes in its own delimiter-neutralised `UntrustedText` region.
- There is one forced strict tool, and no browsing or execution.

**Withheld from the model:** score, view count, answer count, accepted-answer state, tags and URL. Author
data was never acquired.

**What an injection can reach:**
- An injected instruction can at most pick an enum value or a quote that already exists in the source.
- Offsets, labels and lineage are decided by the validator.

**Residual risk.** A verbatim but wrongly labelled quote passes the validator and is caught only by human
evaluation. This is fixture `prompt_injection_text`.

**Adversarial fixtures.** [`first-person-semantic-extraction-fixtures-v1.json`](first-person-semantic-extraction-fixtures-v1.json)
holds 17 synthetic cases, and 13 of them expect zero findings. They test the contract and the validator
only; they are never gold labels.

The validator refuses these traps: quoted complaint, emotional words in code, ambiguous subject, feature
request, hypothetical purchase, past payment and successful workaround.

Three traps pass the validator by construction, and the test names them as evaluation work: plain factual
question, negated pain and prompt injection.

## 13. Evaluation protocol

**Corpus and packs.**
- Corpus: [`stack-overflow-semantic-evaluation-corpus-v1.json`](stack-overflow-semantic-evaluation-corpus-v1.json).
- Packs: `stack-overflow-semantic-label-pack-{development,holdout}-v1.json`, blank.
- Question text is CC BY-SA 4.0 material, so it is not committed. `build_semantic_evaluation_corpus.py --render-working-copy DIR` renders local copies outside the repository and checks every digest.

**Annotation.**
- At least two humans, each on a separate blank copy, blind to each other and to any model output.
- `reference_origin` is required and is one of `HUMAN_OPERATOR`, `HUMAN_EXPERT` or `HUMAN_NON_EXPERT`. `AI_ASSISTED_PROVISIONAL` is refused.

**Agreement.**
- Cohen's κ per extractable label (Krippendorff's α with more than two annotators).
- Also reported: positive-specific agreement and raw counts, because prevalence is extreme.

**Adjudication.**
- A third human or a recorded joint session; both original labels are kept.
- Anything unresolved stays `UNCERTAIN`.
- Adjudication never consults model output.

**Gold.**
- A label is gold for a split only when the agreement floor and the composition gate are both met.
- The gate is at least 4 PRESENT and 4 ABSENT per split, following the Mission 1.26 precedent.
- Otherwise the result is `LABEL_NOT_RELIABLY_ANNOTATABLE` or `REFERENCE_SET_INSUFFICIENT`. It is never fixed by moving records, relabelling, or widening a definition.

**Metrics, reported per label and split.**
- Precision, recall and F1 on PRESENT, with Clopper-Pearson intervals. These are descriptive only.
- Confusion counts, including abstentions.
- Abstention quality.
- Unsupported-assertion rate, split into mechanical (validator refusal) and semantic (human-judged).
- Span and subject correctness.
- Schema validity, where refusals count as failures.
- Run-to-run consistency over three pinned runs; run 1 is the one scored.
- Cost and latency, recorded but never treated as quality.

**Constant classifiers.** The criterion is computed so that all-ABSENT, all-PRESENT and all-ABSTAIN
classifiers each fail.

## 14. Proposed thresholds — `PROPOSED_NOT_AUTHORISED`

**Where they come from.**
- A false PRESENT manufactures a business problem that can travel to a Signal and a Claim. A false ABSENT loses one observation.
- So the thresholds cap false PRESENT with an upper confidence bound, and tolerate conservative misses.
- With zero false PRESENT among n PRESENT predictions, the 95% upper bound is about 3/n.
- Certifying a rate `r_max` therefore needs n ≥ 3/`r_max` PRESENT predictions in the scored split.

| metric | proposed | why |
|---|---|---|
| false PRESENT, upper 95%, `NEGATIVE_EVALUATION_OF_NAMED_SOLUTION` | ≤ 0.10 (needs 30 PRESENT predictions) | writes to a counting dimension no held evidence reaches |
| false PRESENT, upper 95%, `REPORTED_FAILED_ATTEMPT` | ≤ 0.20 (needs 15) | lands on a dimension already held deterministically |
| true PRESENT and true ABSENT | ≥ 1 each | defeats constant classifiers |
| mechanical unsupported assertions accepted | 0 | the validator refuses them by construction |
| validator acceptance rate | ≥ 0.95 | refusals are failures |
| unnecessary abstention on gold-decided records | ≤ 0.10 | abstention must not replace answering |
| run-to-run label flip rate | ≤ 0.10 | an unstable result cannot be audited |
| inter-annotator κ per extractable label | ≥ 0.6 | below it, the definition is the problem |
| recall, cost ceiling, latency | no threshold | descriptive, or fixed in the future execution packet |

**Sufficiency projection.**
- The holdout holds 48 records. It is unlikely to contain 30 PRESENT predictions for `NEGATIVE_EVALUATION_OF_NAMED_SOLUTION`.
- The preregistered outcome for that case is `EVALUATION_INSUFFICIENT`, followed by a separately authorised supplementary acquisition.
- It is never a lowered threshold.

## 15. Frozen Stack Overflow evaluation corpus

**What it is built from.**
- **Resource:** `stack-exchange` / `questions/stackoverflow`, record kind `community_question`, use profile `local-private-research-v1`.
- **Allowed stored fields:** `question_id, site, title, body, tags, creation_label, answer_count, is_answered, accepted_answer_id, score, view_count, question_url, content_licence`.
- **Excluded at acquisition:** `owner` and all its sub-fields, `last_editor`, `comments`, natural-person names, personal identifiers. `author` is null on every record.
- **Licence and attribution:** CC BY-SA 4.0 per item. Attribution is Stack Exchange Network, the licence identifier and the item link.
- **Held records:** 104 (IDs in the manifest), all `VALID` and unsuperseded, from three bounded tag queries: docker over March 2024 (89 records); python on 2024-03-04, two pages (10 and 5).

**What was selected.**
- **Included:** 98. **Excluded:** 6, whose per-item licence the source did not report. The resource-level licence is not assumed to cover them.
- **Split:** within each acquisition cohort, records are ordered by `sha256(seed | normalized_record_id)`. That gives 50 DEVELOPMENT and 48 HOLDOUT. It was frozen before any label, and no model output was used in selection.

**What each record carries.** Identifiers, digests of the stored title and body, the surface digest and
length, code and quote region counts, and counts of residual identifier patterns (email-like, home path,
IPv4-like, handle, long token, URL). It never carries the matched text.

**Enrichment warning.** Label proportions describe these three queries only.

**Expiry.** Normalized records expire from 2027-09-01, and the raw records behind them from 2026-10-01.
Labelling should finish before normalized expiry, or the corpus must be re-frozen under a new version.

## 16. Future provider-egress requirements

**Source permission.**
- Stack Exchange local review v2 sets `external_model_transmission: PERMITTED_WITH_CONDITIONS`.
- The conditions: the provider commits to no training and to bounded, documented retention, and the text is used for inference only.
- The held records were normalized under review v1. A future run must confirm the v2 conditions verify as satisfied.

**Provider permission.**
- The `anthropic` API-key route is APPROVED, on documents retrieved 2026-09-02 with a 180-day review interval.
- The subscription route and the unpaid Gemini route are NOT_APPROVED.
- The runtime does not check review age. **Requalification is therefore a required future step**, and nothing is approved from memory.

**Operator approval** must name all of the following:
- the packet id, version and recomputed sha256;
- the exact `question_id` set;
- the field allowlist and truncation limit;
- the residual-identifier policy;
- the prompt and rubric digests;
- provider, route, endpoint, model and policy version;
- maximum calls, token bounds, USD ceiling and retry policy;
- the exclusions: no training, fine-tuning, embeddings or publication, and no other site or source;
- where outputs are stored and for how long.

**Fields.**
- **May leave:** the rendered surface of an included record.
- **Withheld:** score, views, answer metadata, tags, URL, and the question id (use an opaque packet-local index).
- **Never leaves:** author fields, raw payloads, provenance, workspace and session identifiers, credentials, local paths.

**Residual personal information.** Acquisition removed only structured owner objects; body text can still
carry identifiers. The preferred policy is to exclude or individually review flagged records rather than
redact them, because redaction changes the surface a span must cite. If redaction is chosen, it becomes part
of the surface version and of the packet digest.

**Logging.**
- Telemetry carries ids, tokens and cost only.
- Correlation ids never embed text.
- Provider error bodies must not echo prompts (to verify in N08-B).
- Stored payloads stay local.

**A local model route.**
- **Removes:** the transmission, profile-egress and provider-posture gates.
- **Keeps:** model-processing conditions, attribution, operator approval, evaluation, injection handling and local personal data.
- **Adds:** a weights licence check, a local adapter, and proof that the route is local.
- **Does not remove:** the need for human reference labels.

## 17. Implementation plan

**N08-B.**
- Human labelling of the development pack, with adjudication and agreement and composition verdicts.
- Operator acceptance of the thresholds.
- Operator decision on the `NLP_EXTRACTION` and D-12 wording.
- `packages/semantic-extraction`: prompt regions, strict-tool projection, authorization before serialization, and an extended import ban.
- The egress packet: residual-identifier policy, provider requalification, and a packet-scoped operator approval.
- At most one bounded development run under that approval, with nothing persisted.

**N08-C.**
- Holdout labelling and one preregistered holdout run.
- A verdict per label: PASS, FAIL or EVALUATION_INSUFFICIENT.
- Only on PASS: an ADR and migration for the non-canonical staging tables.
- An ADR for a count Signal over findings and for the INFERRED claim path.
- The independence invariants recorded in N06.
- No Opportunity, no score, no V11.
