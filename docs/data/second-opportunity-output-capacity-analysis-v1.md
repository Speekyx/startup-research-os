# Second Opportunity output capacity analysis

Generated from `second-opportunity-output-capacity-analysis-v1.json`. Do not edit by hand.

**OUTPUT_SCHEMA_HAS_UNBOUNDED_SERIALIZED_SIZE**

Mission 1.84.3. The question was what output-token ceiling the frozen schema justifies. It justifies none: eight required paths are unbounded, so the schema has no finite maximum serialized size and no ceiling can be DERIVED from it. The 3000 Mission 1.84 froze was not merely too small; it was underivable, and so is every other number.

Section 6 is a gate before any arithmetic: a finite maximum requires every variable-length component to be bounded. Eight required array paths contain strings with neither an enum nor a maxLength, so the maximum valid serialized output is unbounded. Inventing a practical maximum is exactly what that gate exists to refuse.

## The gate that stops the arithmetic

- schema `second-opportunity-synthesis-output@1.0.0`, digest `9f8e3849fb0223f5a4c41466d8d8aed994e1d86d446a52e9eca1fd28d80f65e9`
- **FINITE_BOUND = False**
- unbounded required paths: **8**
- **SCHEMA_MAX_SERIALIZED_SIZE = UNBOUNDED**

| path | maxItems | item maxLength | introduced by |
|---|---|---|---|
| `supported_dimensions[]` | 14 | **none** | MISSION_1_31_BASE_SCHEMA |
| `unsupported_dimensions[]` | 14 | **none** | MISSION_1_31_BASE_SCHEMA |
| `supporting_evidence_ids[]` | 20 | **none** | MISSION_1_31_BASE_SCHEMA |
| `supporting_claim_ids[]` | 20 | **none** | MISSION_1_31_BASE_SCHEMA |
| `source_families[]` | 10 | **none** | MISSION_1_31_BASE_SCHEMA |
| `critical_uncertainties[]` | 12 | **none** | MISSION_1_31_BASE_SCHEMA |
| `commercial_claims_supported[]` | 8 | **none** | MISSION_1_31_BASE_SCHEMA |
| `commercial_claims_not_supported[]` | 14 | **none** | MISSION_1_31_BASE_SCHEMA |

## Whose schema this is

All eight unbounded fields come from **MISSION_1_31_BASE_SCHEMA**, byte-identical: True.

Fields Mission 1.84 added: `confidence_classification`, `recommended_next_evidence`, `statement_classifications` — all bounded: **True**.

Mission 1.84.2 recorded the defect as Mission 1.84's. That is right about the FAILURE TO DERIVE and wrong about the cause: the three fields 1.84 added are the only properly bounded ones in the schema, and the eight that make derivation impossible are Mission 1.31's, inherited byte-identically. So 1.84 could not have derived a ceiling from this schema even if it had tried, which it did not.

## A floor, which is not a maximum

NOT the schema maximum, which does not exist. This is the arithmetic statement that whatever the true maximum is, it is AT LEAST this -- the unbounded arrays are held EMPTY here and can only add. A floor is a fact; a practical maximum would be an invention.

- **FLOOR_SERIALIZED_CHARACTERS = 27709**
- FLOOR_UTF8_BYTES = 27709
- digest `25bd267fbedfd56d9d9e46cd9fec8f10140b792ca6889cda199e2bdecad6c9ab`
- exceeds the frozen cap of 3000: **True**

every bounded field at its maximum legal length, every enum at its longest member, the eight unbounded arrays empty, serialized by json.dumps(sort_keys=True) with default separators -- the repository's own canonical path.

Strings are filled with the quotation mark, which JSON escapes to two characters, so a maxLength of N occupies 2N serialized characters plus its quotes. Counting visible characters alone would understate the floor.

At the deployment's one measured ratio of 2.1565 characters per token the floor is roughly 12849 tokens against a frozen cap of 3000. That ratio is an INPUT measurement from Mission 1.31.1 and is NOT an output tokenizer; it is shown to establish the DIRECTION of the comparison and is not used to derive any ceiling.

### Dominant fields

| field | serialized characters | bounded |
|---|---|---|
| `statement_classifications` | 16133 | True |
| `recommended_next_evidence` | 4861 | True |
| `evidence_bound_reasoning_summary` | 1838 | True |
| `hypothesis_statement` | 1226 | True |
| `observed_need` | 819 | True |
| `candidate_intervention_class` | 634 | True |
| `independence_status` | 625 | True |
| `reliability_status` | 624 | True |

`statement_classifications` is 16133 of the floor's 27709 characters, about 58 per cent, and it is one of the three fields Mission 1.84 added. It is properly bounded; it is simply large.

## Tokens

- **EXACT_MAX_OUTPUT_TOKEN_COUNT = NOT_ESTABLISHED**
- exact tokenizer available: False
- empirical ratio: 2.1565, classified `EMPIRICAL_LOWER_INFORMATION_BOUND`

no tokenizer for claude-sonnet-5 is installed in this environment, none is held, and section 15 forbids both a network request to tokenize and installing an unreviewed dependency to obtain a convenient number.

Section 16. A characters-per-token ratio that is too HIGH divides the character count by too much and UNDERESTIMATES tokens, which is the unsafe direction for a capacity ceiling. 2.1565 came from one INPUT measurement of a prompt whose composition differs from this output, so it may be too high here and must not be multiplied by a margin as if it were a tokenizer.

**DERIVED_MIN_OUTPUT_TOKEN_CAPACITY = NOT_DERIVABLE**. **SELECTED_MAX_OUTPUT_TOKENS = NONE**.

## What was not done

The failed 18-of-20 response did not influence which fields are kept. Reducing maxItems because field 20 went missing would be shaping a contract around one rejected answer.

## Options, none implemented and none recommended

Section 18. Offered, none implemented, and none recommended as though decided. Each is an architecture choice with a different cost, and picking one is not capacity arithmetic.

| option | what | makes the schema finite | cost |
|---|---|---|---|
| `BOUND_THE_EIGHT_ITEM_STRINGS` | add a maxLength to the item schema of each of the eight unbounded arrays | **True** | a schema version bump and a gate version bump, and a judgement about what each field's longest legitimate value is -- an id, a dimension name and a free-text uncertainty do not share one sensible bound |
| `REDUCE_STATEMENT_CLASSIFICATIONS` | lower maxItems or the statement maxLength on the largest field | **False** | changes the output CONTRACT and the gate version, and does not remove the unboundedness |
| `REFERENCE_RATHER_THAN_DUPLICATE` | have statement_classifications carry statement IDENTIFIERS rather than repeat the statement text | **False** | a different output representation, and the ids still need bounding |
| `SPLIT_THE_TASK` | separate synthesis from classification into two deterministic stages | **False** | a second call, which this arc's whole discipline is built to avoid |
| `ACCEPT_AN_OPERATOR_DECLARED_CEILING` | the operator states a ceiling explicitly as their own judgement rather than as a derived bound | **False** | the packet would then record a ceiling that is declared rather than derived, and it must say so in those words |

## Nothing else moved

- representation `2528a56a4a9e873bfd04662aeb52916eb80faafe10ab085e716cbdcee77c5b72` (3604 characters), unchanged
- prompt `af5289494416139d302eed704c12b9c53ab2547dca336e2ca4a834ec936c5080`, unchanged
- provider `anthropic`, posture **APPROVED**
- subscription route posture NOT_APPROVED, used False
- model `claude-sonnet-5`, selection changed False
- pricing `anthropic-published-2026-09-02`, changed False
- TED transmission PERMITTED_WITH_CONDITIONS, packet gate AVAILABLE

The deployment still configures exactly one text tier; FAST and BALANCED bind the literal string 'null'. Selection is unchanged, and this mission does not mix an output-capacity repair with a model migration.

**RETENTION_REPAIR_VERIFIED = True.** The Mission 1.84.2 closure suite drives seven synthetic terminal paths through the real Gateway with scripted transports and asserts each retains what it can: raw response and its digest, parsed output and its digest, usage, and the terminal outcome. A tripwire test replaces UrllibTransport.__init__ and asserts no fixture constructs the real transport. 31 tests, no network.

## V1 and V2

- V1 `570657e1a862a96742925f6a5e5a17b0e1860bf9f2f0b8315fa33c560496da92`, unchanged True
- **EXECUTION_APPROVAL_CONSUMED = True**, further calls False
- guard refuses V1: True (`EXECUTION_APPROVAL_ALREADY_CONSUMED`), permits a new digest: True
- **EXECUTION_PACKET_V2_CREATED = False**

A packet binds MAX_OUTPUT_TOKENS. Any value chosen here would be invented rather than derived, which is the defect this mission was called to repair. Producing V2 anyway would repeat Mission 1.84's error with better paperwork.

## Accounting

| counter | value |
|---|---|
| MODEL_CALLS | 0 |
| PROVIDER_REQUESTS | 0 |
| REMOTE_TEST_CALLS | 0 |
| TED_BYTES_SENT | 0 |
| CANONICAL_RESEARCH_MUTATION | 0 |
| OPPORTUNITIES_CREATED | 0 |
| SCORES_PERSISTED | 0 |
| EMBEDDINGS_CREATED | 0 |
| SCHEMA_CHANGES | 0 |
| DEPENDENCIES_INSTALLED | 0 |
| NETWORK_REQUESTS | 0 |

**Next: OPERATOR_DECISION_ON_OUTPUT_SCHEMA_BOUNDEDNESS.** No execution packet can be prepared until the schema has a finite maximum or the operator declares a ceiling as their own judgement. Both are decisions, not arithmetic, and neither is taken here.
