# Mission 1.84.4 — Second Opportunity Bounded Output Contract V1.1

**`BOUNDED_SCHEMA_READY_TOKEN_CEILING_REQUIRES_OPERATOR_DECISION`**

The eight unbounded item types are bounded, the contract has an exact finite maximum for the first
time, and no token ceiling was chosen. The remaining question is a different and much smaller one
than the question Mission 1.84.3 raised.

```
START_COMMIT   bace04e
BRANCH         sprint-1/mission-1.84.4

OPERATOR_DECISION   BOUND_THE_EIGHT_UNBOUNDED_ITEM_TYPES
OPERATOR_REJECTED   OPERATOR_DECLARED_ARBITRARY_OUTPUT_TOKEN_CEILING
```

## The two contracts

```
old schema   second-opportunity-synthesis-output@1.0.0
             9f8e3849fb0223f5a4c41466d8d8aed994e1d86d446a52e9eca1fd28d80f65e9
             8 unbounded required paths, unchanged, still readable

new schema   second-opportunity-synthesis-output@1.1.0
             ec789d1be7d525bf6e498bf61e8a0596ac4582e24e8b45073b3f9ac1cca8b988
             0 unbounded required paths

old gate     second-opportunity-output-gate@1.0.0
new gate     second-opportunity-output-gate@1.1.0
```

**v1.0.0 was not mutated in place, and a gate check now enforces that it keeps its defect.** A
historical execution has to keep resolving against the contract it actually used: repairing v1.0.0
would make the frozen prompt document's `OUTPUT_SCHEMA_SHA256` name a schema nobody sent, and
Mission 1.84.3's finding would stop being reproducible from the repository that recorded it.

## The eight, and what each became

| path | old item | new item | class |
|---|---|---|---|
| `supported_dimensions[]` | `string` | `enum`, the 14 `EvidenceDimension` values | CLOSED_VOCABULARY |
| `unsupported_dimensions[]` | `string` | the same enum | CLOSED_VOCABULARY |
| `supporting_evidence_ids[]` | `string` | canonical UUID pattern, `maxLength` 36 | CANONICAL_IDENTIFIER |
| `supporting_claim_ids[]` | `string` | canonical UUID pattern, `maxLength` 36 | CANONICAL_IDENTIFIER |
| `source_families[]` | `string` | registry slug pattern, `maxLength` 128 | BOUNDED_IDENTIFIER |
| `critical_uncertainties[]` | `string` | `minLength` 1, `maxLength` 500 | BOUNDED_NARRATIVE |
| `commercial_claims_supported[]` | `string` | `maxLength` 300 | BOUNDED_NARRATIVE |
| `commercial_claims_not_supported[]` | `string` | `maxLength` 300 | BOUNDED_NARRATIVE |

**Four instruments, because the fields differ in kind.** One `maxLength` applied eight times would
have been a number rather than a contract: it would have bounded the SIZE of a dimension name and
left `MARKET_DEMAND` acceptable, which is the exact transformation the semantic gate exists to
refuse. **Every `maxItems` is unchanged**, no field was added, removed or reordered, and the
`required` list is byte-identical.

### Where each bound came from

**Dimensions** are derived in code from `EvidenceDimension` rather than transcribed — §6 forbids a
manually-maintained second list where a canonical source exists, and that enum is what the
persistence gate itself compares against. An unknown dimension is now refused **however short it
is**, which is the property a length could never give.

**Evidence ids and Claim ids were determined separately**, as §7 and §8 require. Both resolve to
`_UuidId` in `sros_contracts.ids`, whose constructor canonicalises through `str(uuid.UUID(value))`,
so the canonical form is lowercase and hyphenated. They agree because they subclass the same
canonical base, **not because today's rows happen to look alike** — and the test asserts the
pattern accepts what each identity class actually generates rather than trusting the regex.

**`source_families` was the one §9 warned about, and the wrong registry fits.** There are two
different `source_family` vocabularies in this repository: the source catalog's
(`public_procurement`, `economic_data`, `knowledge`, …) and a diagnostic script's
(`encyclopedia_readership`, `community_qa`, `official_statistics`). They share the string
`public_procurement`, which is exactly the coincidence that would have made a wrong binding look
right. The production preparation path reads `registry.sources.source_family`, which carries a
**foreign key** to `registry.registry_entries`, whose `registry_entries_id_slug_check` is the
grammar that actually decides which family ids can exist.

**And it is a registry rather than a closed vocabulary**, which decides the instrument.
`domain.v1.json` lists `source_family` under `registries` and not under `closed_enums`, and the
repository's own rule is that adding a registry entry must never require a contract change.
Fifteen families are registered today; freezing them into an enum would make the schema refuse a
true answer the moment a sixteenth is. So the bound is the slug grammar and its 128-character
maximum, and **the gate reads that pattern out of the migration** rather than trusting a copy.

**The commercial claim fields were inspected before being bounded, and the answer was not the one
their JSON type suggests.** §11 required the semantics to be established: the Mission 1.31.1 output
carries fourteen sentences — *"That a buyer with budget authority exists in this space"* — and the
persistence gate audits both fields as PROSE through the commercial-vocabulary guard, which needs a
sentence to read. **Narrative branch**, operator length 300.

## The bound needed something to enforce it

`LlmGateway._validate_structured` checks that every `required` key is PRESENT and stops there — its
own docstring says full JSON Schema validation *"arrives with the first real provider"*. **So
nothing in this repository has ever enforced a `maxLength`, an `enum`, a `maxItems` or a `pattern`
on a model's answer.** A bound only the provider is told about is a request, not a contract.

`sros_opportunity.schema_validation` implements exactly the keyword set these two schemas use, with
**no dependency added** — `jsonschema` is not in this workspace and §21 forbids installing an
unreviewed package. `unsupported_keywords` names anything outside that set, so a future schema
keyword cannot be silently ignored by a validator that looks like it checked; it returns empty for
both contracts today, and the probe adds a keyword to confirm the report fires.

## Finite, and the maximum measured

```
FINITE_BOUND                 true
UNBOUNDED_PATHS              0   (v1.0.0: 8)
MAX_INSTANCE_SCHEMA_VALID    true, through the real v1.1.0 validator
MAX_VALID_OUTPUT_CHARACTERS  309729
MAX_VALID_OUTPUT_UTF8_BYTES  309729
MAX_VALID_OUTPUT_SHA256      e1a62b812f115b3549b5c3c5b8605f2c8052b998cce5d89ac7b60cee5af71705
ASCII-fill diagnostic        56929   (NOT the maximum)
```

**The worst-case fill is a non-BMP character, and it matters by a factor of five.** Under
`ensure_ascii` a character like U+1F600 serialises as a surrogate pair of **twelve** characters for
one character of budget. Mission 1.84.3's floor used the quotation mark, which costs two; a maximum
computed that way would be 56929, and **understating the maximum is the unsafe direction for a
capacity ceiling**. Both numbers are reported, with the smaller one labelled a diagnostic.

There are no optional fields to include: `additionalProperties` is false and all twenty properties
are required.

## What actually consumes the capacity

| field | max characters | share |
|---|---:|---:|
| `statement_classifications` | 88133 | 28.45% |
| `critical_uncertainties` | 72074 | 23.27% |
| `commercial_claims_not_supported` | 50491 | 16.30% |
| `commercial_claims_supported` | 28863 | 9.32% |
| `recommended_next_evidence` | 28861 | 9.32% |
| `evidence_bound_reasoning_summary` | 10838 | 3.50% |

**Bounding the eight moved the dominant consumers somewhere else, and that is §20's finding.** The
five identifier and vocabulary paths — both dimension arrays, both id arrays and `source_families` —
now contribute **1.31% between them**. A future contract change aimed at capacity belongs in the
narrative fields, and specifically in `statement_classifications`, which is not one of the eight and
was already bounded.

**A character-class restriction on the narrative fields would recover roughly five sixths of the
maximum, and it was not applied.** The operator authorised a LENGTH for those fields and nothing
else; a pattern restricting them to printable characters is a different axis of constraint nobody
decided, and it would also refuse legitimate accented text. The consequence is measured rather than
hidden.

## The ceiling was not chosen, and that is the honest half

```
EXACT_TOKENIZER_AVAILABLE          false
EXACT_MAX_OUTPUT_TOKEN_COUNT       NOT_ESTABLISHED
SAFE_TOKEN_BOUND_AVAILABLE         false
DERIVED_MIN_OUTPUT_TOKEN_CAPACITY  NOT_DERIVABLE
SELECTED_MAX_OUTPUT_TOKENS         NONE
```

`tokenizers`, `tiktoken`, `transformers`, `sentencepiece` and the `anthropic` SDK are all absent —
checked rather than asserted, by a test. §21 forbids installing an unreviewed dependency for a
convenient number, and a network request to tokenize is forbidden outright.

**§22 requires a conversion proven in the correct direction, and nothing held establishes one.**
*One character is at most one token* is false for any subword tokenizer. *One byte is at most one
token* holds for a byte-level BPE, where every token decodes to at least one byte — and **no held
first-party document says which tokenizer family `claude-sonnet-5` uses**, so that premise would be
an assumption wearing the costume of a contract. It would also ignore the framing tokens the API
adds around a tool call, which are not characters of the output at all.

The 2.1565 characters-per-token figure is carried forward exactly as Mission 1.84.3 recorded it —
`EMPIRICAL_LOWER_INFORMATION_BOUND`, an INPUT measurement, with the warning that a ratio too HIGH
underestimates tokens — and **`empirical_ratio_use_here` is `NONE`**, enforced by the gate.

### The model capability

`CONFIGURED_OUTPUT_TOKEN_CAPABILITY = NOT_ESTABLISHED`. What is held is
`AnthropicProvider.max_output_tokens = 4096`, **our adapter's default**, plus a compose environment
binding provider and model and stating no token capability. No live model catalogue was fetched.
Recording 4096 as the model's capability would turn a number this repository chose into a
discovered fact, and §23 adds that even a known capability would be a ceiling on what the model
CAN emit and never evidence that this schema fits inside it.

## The prompt moved with the schema

```
prompt v1.0.0   af5289494416139d302eed704c12b9c53ab2547dca336e2ca4a834ec936c5080  unchanged
prompt v1.1.0   2f60c61f63cda410b9f60e3eafd9676f983e7ff0220245c03c88136511ac7e82
```

The rendered prompt hash covers the output schema, so bounding the contract moves it whether or not
a rendered byte changed. **Rendered bytes changed too**: the v1.1.0 system region states the
bounds, because a model refused for a 501-character element was never told the limit was 500.

**Semantic diff: 21 lines added, 0 removed**, and the v1.1.0 system region **extends v1.0.0
verbatim** — asserted with `startswith`, so a research or refusal sentence cannot have been reworded
while nobody was looking. `trusted_context`, the untrusted region and `task` are byte-identical. The
added block ends by saying the limits are on FORM and never on how much the model may refuse to
conclude, so a length cap cannot be read as pressure to assert more with less hedging.

## What did not move

**TED representation `2528a56a4a9e873bfd04662aeb52916eb80faafe10ab085e716cbdcee77c5b72`, 3604
characters, unchanged.** Recomputed from live state through the production serializer rather than
copied. §15 makes a moved digest a hard stop before capacity derivation, and the schema repair does
not authorise changing source material.

**`RETENTION_REPAIR_VERIFIED = true`.** The Mission 1.84.2 closure suite re-run: 31 tests, seven
synthetic terminal paths through the real Gateway with scripted transports, the tripwire replacing
`UrllibTransport.__init__` still proving no fixture constructs the real transport. No network.

**V1 `570657e1…` is byte-identical and still consumed.** The guard refuses its digest with
`EXECUTION_APPROVAL_ALREADY_CONSUMED` and **permits an unseen one**, so a genuinely new packet is
not blocked merely because V1 was spent. The consumption record was not reset, and the frozen packet
still records no approval inside itself.

**`EXECUTION_PACKET_V2_CREATED = false`, so there is no V2 digest.** §24 permits one only when a
defensible token capacity is established; the first condition fails, so the model-capability and
pricing conditions are not reached and §25's recompute did not run. `PREVIOUS_APPROVAL_REUSABLE`
is false and `NEW_APPROVAL_REQUIRED` is true whenever a V2 does exist.

## Accounting

```
model calls          0        provider requests    0
network requests     0        remote test calls    0
TED bytes sent       0        dependencies added   0
canonical mutations  0        Opportunities        0
```

Every counter in §29 matches exactly: 325 / 325 / 60 / 91 / 92 / 112 / 4 / 0 / 1 / 2 / 14 / 0 / 71,
and `scoring.scores` is still absent.

## Verification

`ruff format --check` and `ruff check` clean over 995 files. Two `S105` false positives suppressed
with the reason stated — the flagged "token" is an output-token count and not a credential — and
one `SIM102` collapsed by hand with the probe re-run afterwards, because Mission 1.83 found that a
mechanical collapse once folded a sibling check inside a `raise`. `mypy` clean over 200 files.
Contracts, catalog and source registry checks clean; 29 sources, 45 evidence records, 0 warnings.

**3831 bare-python tests across 9 packages. 3591 pytest tests across 9 packages**, 13 skipped, with
the database unchanged across 29 tenant tables and 11 rows appended to 1 append-only table. **87 new
tests.** **68 CI gates**, one of them new.

**Probe: 89 violations caught, 0 escaped, 9 of 9 positive controls, every file proved restored.**
The cases mutate the shipped documents on disk AND the live schema AND the predecessor schema, and
run the whole `validate()` the way CI does rather than calling individual checks. Among them: four
arbitrary round-number ceilings, an unsafe byte-to-token conversion, an adapter default promoted to
a capability, v1.0.0 repaired in place, a dimension bound by length, `source_families` frozen into
an enum, a reduced `maxItems`, a dropped required field, and the prompt digest left unchanged while
the schema moved.

## Outcome and next

**`BOUNDED_SCHEMA_READY_TOKEN_CEILING_REQUIRES_OPERATOR_DECISION`.**

**Next: `OPERATOR_DECISION_ON_OUTPUT_TOKEN_CONVERSION`.** The question left is strictly smaller than
the one Mission 1.84.3 raised, and it is a different kind of question: the contract now has an exact
finite maximum measured in characters and bytes, and what is missing is an authorised way to turn
that count into a token ceiling. Three routes exist and each is a decision rather than arithmetic:
install and review a tokenizer; accept a stated byte-to-token bound as the operator's own judgement
with its basis recorded; or bound the narrative fields further — the field analysis says exactly
where — so the maximum falls far enough that any plausible conversion is comfortable.

**Do not execute any packet, do not retry V1, and do not persist Opportunity #2.** Mission 1.84.5
was not started.
