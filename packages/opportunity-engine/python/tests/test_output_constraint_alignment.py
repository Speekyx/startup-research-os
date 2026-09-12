"""Mission 1.84.8. The prompt states what the schema enforces, and the schema still decides.

Four things this file defends, against the live schema and the live renderer.

THE BLOCK IS DERIVED. The same schema renders byte-identical text; moving a bound in a schema fixture
moves the text; the bound V2 was refused against is stated because the schema carries it, and a note,
the renderer or the v1.2.0 section cannot carry a number of their own.

EVERY GENERATION-RELEVANT BOUND IS STATED, not only the one V2 was refused on, and no stanza states a
number its own field does not carry.

THE VALIDATOR STILL DECIDES. Synthetic answers below, at and one over each bound, the brief's cases A
to H, pass or fail the live v1.1.0 validator exactly as they did before the prompt changed, and an
answer that fails is refused whole.

GATE 72 REFUSES THE SHORTCUTS, through the whole `validate()` against copies of its two records, and
through its code-level checks against a schema, a block or a source edited in memory.
"""

from __future__ import annotations

import copy
import hashlib
import importlib.util
import json
import pathlib
import re
import shutil

import pytest
from sros_opportunity.output_constraints import (
    INTERNAL_VALIDATOR_ONLY,
    MUST_BE_EXPLICIT_IN_PROMPT,
    constraint_inventory,
    is_explicit,
    prompt_stanzas,
    render_output_constraints,
)
from sros_opportunity.schema_validation import schema_violations
from sros_opportunity.second_opportunity import (
    BOUNDED_OUTPUT_CONTRACT_RULES,
    OUTPUT_CONSTRAINT_NOTES_V1_2,
    SECOND_OPPORTUNITY_GATE_VERSION_V1_1,
    SECOND_OPPORTUNITY_OUTPUT_CONSTRAINTS_V1_2,
    SECOND_OPPORTUNITY_OUTPUT_SCHEMA_V1_1,
    SECOND_OPPORTUNITY_SYSTEM,
    SECOND_OPPORTUNITY_SYSTEM_V1_1,
    SECOND_OPPORTUNITY_SYSTEM_V1_2,
)

REPO_ROOT = pathlib.Path(__file__).resolve().parents[4]
GATE_PATH = (
    REPO_ROOT
    / "infrastructure"
    / "scripts"
    / "render_second_opportunity_output_constraint_alignment.py"
)
SCHEMA = SECOND_OPPORTUNITY_OUTPUT_SCHEMA_V1_1
NOTES = OUTPUT_CONSTRAINT_NOTES_V1_2
SUMMARY = "evidence_bound_reasoning_summary"
EVIDENCE_ID = "0b407e80-336a-4b71-8a59-09f0464bf43f"
CLAIM_ID = "d25bd256-49a1-494f-b6f8-4f1c3271d78e"


def _load_gate():
    spec = importlib.util.spec_from_file_location("gate_72_under_test", GATE_PATH)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


GATE = _load_gate()


def _render(schema=SCHEMA, notes=NOTES) -> str:
    return render_output_constraints(schema, notes)


def _numbers_in(node: dict) -> set[int]:
    """Every bound a schema node carries, and the field count of any object inside it."""
    found: set[int] = set()
    for keyword in ("minLength", "maxLength", "minItems", "maxItems"):
        if keyword in node:
            found.add(int(node[keyword]))
    if isinstance(node.get("properties"), dict):
        found.add(len(node["properties"]))
        for sub in node["properties"].values():
            found |= _numbers_in(sub)
    if isinstance(node.get("items"), dict):
        found |= _numbers_in(node["items"])
    return found


# ================================================================== the block is derived


class TestTheBlockIsDerived:
    def test_the_same_schema_renders_byte_identical_text(self) -> None:
        first = _render()
        assert _render() == first
        assert _render(copy.deepcopy(SCHEMA), dict(NOTES)) == first
        assert first == SECOND_OPPORTUNITY_OUTPUT_CONSTRAINTS_V1_2

    def test_the_reasoning_summary_bound_is_stated_because_the_schema_carries_it(self) -> None:
        bound = SCHEMA["properties"][SUMMARY]["maxLength"]
        assert bound == 900, "the operator kept the bound, and this mission does not move it"
        stanza = prompt_stanzas(SECOND_OPPORTUNITY_SYSTEM_V1_2)[SUMMARY]
        assert stanza == f"at most {bound} characters"

    @pytest.mark.parametrize("bound", [750, 901, 1200])
    def test_moving_the_bound_in_a_fixture_moves_the_instruction(self, bound) -> None:
        fixture = copy.deepcopy(SCHEMA)
        fixture["properties"][SUMMARY]["maxLength"] = bound
        assert prompt_stanzas(_render(fixture))[SUMMARY] == f"at most {bound} characters"
        assert _render(fixture) != _render()

    def test_rewording_a_description_changes_nothing(self) -> None:
        fixture = copy.deepcopy(SCHEMA)
        fixture["properties"]["recommended_next_evidence"]["description"] = "Reworded."
        assert _render(fixture) == _render()

    def test_the_sentinel_comes_from_the_schema(self) -> None:
        stanza = prompt_stanzas(_render())["target_actor_if_supported"]
        assert "the exact string UNKNOWN_NOT_SUPPORTED" in stanza
        fixture = copy.deepcopy(SCHEMA)
        node = fixture["properties"]["target_actor_if_supported"]
        node["description"] = node["description"].replace(
            "UNKNOWN_NOT_SUPPORTED", "NO_ACTOR_SUPPORTED"
        )
        assert "NO_ACTOR_SUPPORTED" in prompt_stanzas(_render(fixture))["target_actor_if_supported"]

    def test_a_vocabulary_bound_made_binding_appears(self) -> None:
        fixture = copy.deepcopy(SCHEMA)
        vocabulary = len(fixture["properties"]["supported_dimensions"]["items"]["enum"])
        assert "elements" not in prompt_stanzas(_render())["supported_dimensions"]
        fixture["properties"]["supported_dimensions"]["maxItems"] = vocabulary - 1
        stanza = prompt_stanzas(_render(fixture))["supported_dimensions"]
        assert f"at most {vocabulary - 1} elements" in stanza

    def test_a_note_carrying_a_digit_is_refused(self) -> None:
        with pytest.raises(ValueError, match="digit"):
            _render(notes={SUMMARY: "at most 900 characters, as the operator said"})

    def test_a_note_naming_no_real_field_is_refused(self) -> None:
        with pytest.raises(ValueError, match="not a field"):
            _render(notes={"critical_uncertainties": "see the reasoning_summary_field"})

    def test_a_note_for_a_field_the_schema_lacks_is_refused(self) -> None:
        with pytest.raises(ValueError, match="does not carry"):
            _render(notes={"reasoning": "a note for nothing"})

    def test_an_unknown_keyword_is_refused_rather_than_rendered_silently(self) -> None:
        fixture = copy.deepcopy(SCHEMA)
        fixture["properties"]["critical_uncertainties"]["uniqueItems"] = True
        with pytest.raises(ValueError, match="cannot classify"):
            _render(fixture)

    def test_the_renderer_reads_nothing_but_the_schema_and_carries_no_number(self) -> None:
        GATE._check_renderer()


# ================================================================== every bound is stated


def _generation_relevant():
    return [
        c for c in constraint_inventory(SCHEMA) if c.constraint_class == MUST_BE_EXPLICIT_IN_PROMPT
    ]


class TestEveryGenerationRelevantBoundIsStated:
    def test_every_class_a_constraint_is_explicit_in_v1_2(self) -> None:
        unstated = [
            f"{c.path} {c.keyword}"
            for c in _generation_relevant()
            if not is_explicit(c, SECOND_OPPORTUNITY_SYSTEM_V1_2)
        ]
        assert unstated == []

    def test_v1_1_left_other_narrative_bounds_unstated_too(self) -> None:
        """Mission 1.84.7 exposed one drift. The audit finds the rest before a paid call does."""
        missing = {
            f"{c.path} {c.keyword}"
            for c in _generation_relevant()
            if not is_explicit(c, SECOND_OPPORTUNITY_SYSTEM_V1_1)
        }
        assert f"{SUMMARY} maxLength" in missing
        for other in (
            "subject maxLength",
            "observed_need maxLength",
            "hypothesis_statement maxLength",
            "recommended_next_evidence[] maxLength",
            "statement_classifications[].statement maxLength",
            "critical_uncertainties maxItems",
        ):
            assert other in missing, other

    def test_what_v1_1_stated_is_still_stated(self) -> None:
        for constraint in _generation_relevant():
            if is_explicit(constraint, SECOND_OPPORTUNITY_SYSTEM_V1_1):
                assert is_explicit(constraint, SECOND_OPPORTUNITY_SYSTEM_V1_2), constraint

    def test_no_stanza_states_a_number_its_field_does_not_carry(self) -> None:
        """No duplicate, contradictory or invented bound: every number in a stanza is its own."""
        stanzas = prompt_stanzas(SECOND_OPPORTUNITY_SYSTEM_V1_2)
        for name, node in SCHEMA["properties"].items():
            stated = {int(n) for n in re.findall(r"\b\d+\b", stanzas[name])}
            assert stated <= _numbers_in(node), (name, stated - _numbers_in(node))

    def test_the_hand_written_v1_1_block_is_not_carried_alongside(self) -> None:
        assert BOUNDED_OUTPUT_CONTRACT_RULES not in SECOND_OPPORTUNITY_SYSTEM_V1_2
        assert SECOND_OPPORTUNITY_SYSTEM_V1_2.count("THE OUTPUT CONTRACT IS BOUNDED") == 1

    def test_v1_2_extends_v1_0_0_verbatim_and_v1_1_is_untouched(self) -> None:
        assert SECOND_OPPORTUNITY_SYSTEM_V1_2.startswith(SECOND_OPPORTUNITY_SYSTEM)
        frozen = json.loads(
            (REPO_ROOT / "docs" / "data" / "second-opportunity-synthesis-prompt-v2.json").read_text(
                encoding="utf-8"
            )
        )
        assert frozen["SYSTEM_INSTRUCTION"] == SECOND_OPPORTUNITY_SYSTEM_V1_1

    def test_the_schema_and_the_gate_did_not_move(self) -> None:
        digest = hashlib.sha256(json.dumps(SCHEMA, sort_keys=True).encode("utf-8")).hexdigest()
        assert digest == "ec789d1be7d525bf6e498bf61e8a0596ac4582e24e8b45073b3f9ac1cca8b988"
        assert SECOND_OPPORTUNITY_GATE_VERSION_V1_1 == "second-opportunity-output-gate@1.1.0"

    def test_the_drift_property_holds_on_the_live_schema(self) -> None:
        counts = GATE.drift_property()
        assert counts["A_MUTATIONS"] == counts["A_MUTATIONS_MOVING_THE_PROMPT"]
        assert counts["A_MUTATIONS"] == len(_generation_relevant())
        assert counts["OTHER_CLASS_MUTATIONS"] == counts["OTHER_CLASS_MUTATIONS_LEAVING_THE_PROMPT"]
        assert counts["OTHER_CLASS_MUTATIONS"] > 0
        assert counts["VOCABULARY_BOUNDS_MADE_BINDING_MOVING_THE_PROMPT"] == 2
        assert counts["DESCRIPTIONS_REWORDED"] > 0


# ================================================================== the validator still decides


def _valid_output() -> dict:
    return {
        "decision": "FORM_HYPOTHESIS",
        "subject": "ted-eu:CPV-class:9261",
        "target_actor_if_supported": "UNKNOWN_NOT_SUPPORTED",
        "observed_need": "n",
        "candidate_intervention_class": "c",
        "hypothesis_statement": "h",
        "supported_dimensions": ["MARKET_ACTIVITY"],
        "unsupported_dimensions": ["WILLINGNESS_TO_PAY"],
        "supporting_evidence_ids": [EVIDENCE_ID],
        "supporting_claim_ids": [CLAIM_ID],
        "source_families": ["public_procurement"],
        "independence_status": "i",
        "reliability_status": "r",
        SUMMARY: "s",
        "critical_uncertainties": ["u"],
        "commercial_claims_supported": [],
        "commercial_claims_not_supported": ["p"],
        "recommended_next_evidence": ["o"],
        "confidence_classification": "EXPLORATORY",
        "statement_classifications": [
            {"statement": "s", "classification": "HYPOTHESIS_TO_VALIDATE"}
        ],
    }


def _with(field: str, value: object) -> dict:
    output = _valid_output()
    output[field] = value
    return output


PROPERTIES = SCHEMA["properties"]
SUMMARY_MAX = PROPERTIES[SUMMARY]["maxLength"]
UNCERTAINTY_MAX = PROPERTIES["critical_uncertainties"]["items"]["maxLength"]
CLAIM_MAX = PROPERTIES["commercial_claims_not_supported"]["items"]["maxLength"]
UNCERTAINTY_COUNT = PROPERTIES["critical_uncertainties"]["maxItems"]
STATEMENT_COUNT = PROPERTIES["statement_classifications"]["maxItems"]
ONE_STATEMENT = {"statement": "s", "classification": "HYPOTHESIS_TO_VALIDATE"}

COMPLIANCE = [
    ("A summary one under", _with(SUMMARY, "x" * (SUMMARY_MAX - 1)), []),
    ("B summary at the bound", _with(SUMMARY, "x" * SUMMARY_MAX), []),
    (
        "C summary one over",
        _with(SUMMARY, "x" * (SUMMARY_MAX + 1)),
        [f"{SUMMARY}: {SUMMARY_MAX + 1} characters exceeds maxLength {SUMMARY_MAX}"],
    ),
    ("D uncertainty at the bound", _with("critical_uncertainties", ["x" * UNCERTAINTY_MAX]), []),
    (
        "E uncertainty one over",
        _with("critical_uncertainties", ["x" * (UNCERTAINTY_MAX + 1)]),
        [
            f"critical_uncertainties[0]: {UNCERTAINTY_MAX + 1} characters exceeds maxLength "
            f"{UNCERTAINTY_MAX}"
        ],
    ),
    (
        "F commercial statement at the bound",
        _with("commercial_claims_not_supported", ["x" * CLAIM_MAX]),
        [],
    ),
    (
        "G commercial statement one over",
        _with("commercial_claims_not_supported", ["x" * (CLAIM_MAX + 1)]),
        [
            f"commercial_claims_not_supported[0]: {CLAIM_MAX + 1} characters exceeds maxLength "
            f"{CLAIM_MAX}"
        ],
    ),
    (
        "H too many uncertainties",
        _with("critical_uncertainties", ["u"] * (UNCERTAINTY_COUNT + 1)),
        [
            f"critical_uncertainties: {UNCERTAINTY_COUNT + 1} items exceeds maxItems {UNCERTAINTY_COUNT}"
        ],
    ),
    (
        "H too many classified statements",
        _with("statement_classifications", [ONE_STATEMENT] * (STATEMENT_COUNT + 1)),
        [
            f"statement_classifications: {STATEMENT_COUNT + 1} items exceeds maxItems "
            f"{STATEMENT_COUNT}"
        ],
    ),
]


class TestTheValidatorStillDecides:
    def test_the_bounds_are_the_ones_the_operator_kept(self) -> None:
        assert (SUMMARY_MAX, UNCERTAINTY_MAX, CLAIM_MAX) == (900, 500, 300)

    def test_the_minimal_answer_is_valid(self) -> None:
        assert schema_violations(_valid_output(), SCHEMA) == []

    @pytest.mark.parametrize(
        ("output", "expected"), [c[1:] for c in COMPLIANCE], ids=[c[0] for c in COMPLIANCE]
    )
    def test_a_synthetic_answer_passes_or_fails_exactly_at_the_bound(self, output, expected):
        assert schema_violations(output, SCHEMA) == expected

    def test_an_answer_over_a_stated_bound_is_refused_whole_and_not_trimmed(self) -> None:
        output = _with(SUMMARY, "x" * (SUMMARY_MAX + 1))
        assert schema_violations(output, SCHEMA)
        assert len(output[SUMMARY]) == SUMMARY_MAX + 1
        assert f"at most {SUMMARY_MAX} characters" in SECOND_OPPORTUNITY_SYSTEM_V1_2

    def test_the_v2_facts_are_reconfirmed_from_what_v2_retained(self) -> None:
        facts = GATE.v2_facts()
        assert (facts["PROVIDER_REQUESTS"], facts["MODEL_CALLS"], facts["RETRIES"]) == (1, 1, 0)
        assert facts["FALLBACKS"] == 0
        assert facts["STOP_REASON"] == "tool_use"
        assert (facts["INPUT_TOKENS"], facts["OUTPUT_TOKENS"], facts["THINKING_TOKENS"]) == (
            8939,
            3914,
            0,
        )
        assert facts["ACTUAL_COST"] == 0.057018
        assert facts["FAILED_STAGE"] == "5_schema_validation_v1_1_0"
        assert facts["SCHEMA_VIOLATIONS"] == [f"{SUMMARY}: 1113 characters exceeds maxLength 900"]
        assert len(facts["STAGES_NOT_REACHED"]) == 5
        assert facts["CANONICAL_PERSISTENCE"] is False
        assert facts["APPROVAL_CONSUMED"] is True
        assert facts["DISCREPANCIES"] == []


# ================================================================== gate 72, whole


def test_the_shipped_records_validate() -> None:
    GATE.validate()


def test_the_rendered_pages_are_current() -> None:
    assert GATE.main(["--check"]) == 0


@pytest.fixture
def world(tmp_path, monkeypatch):
    for name in ("ALIGNMENT", "PROMPT"):
        source = getattr(GATE, name)
        target = tmp_path / source.name
        shutil.copyfile(source, target)
        monkeypatch.setattr(GATE, name, target)
    return tmp_path


def _read(path: pathlib.Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _edit(which: str, fn) -> None:
    path = GATE.ALIGNMENT if which == "alignment" else GATE.PROMPT
    doc = _read(path)
    fn(doc)
    path.write_text(json.dumps(doc, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def _set(*keys_and_value):
    *keys, value = keys_and_value

    def apply(doc):
        node = doc
        for key in keys[:-1]:
            node = node[key]
        node[keys[-1]] = value

    return apply


def _row(path: str, keyword: str, field: str, value: object):
    def apply(doc):
        row = next(
            r for r in doc["CONSTRAINT_INVENTORY"] if r["path"] == path and r["keyword"] == keyword
        )
        row[field] = value

    return apply


def _reword_statement(doc) -> None:
    lines = doc["OPERATOR_DECISION"]["OPERATOR_STATEMENT"]
    lines[lines.index("The rejected V2 answer MUST NOT be rescued.")] = (
        "The rejected V2 answer MAY be rescued."
    )


def _replace_in_system(old: str, new: str):
    def apply(doc):
        assert old in doc["SYSTEM_INSTRUCTION"]
        doc["SYSTEM_INSTRUCTION"] = doc["SYSTEM_INSTRUCTION"].replace(old, new)

    return apply


REFUSED = [
    ("schema changed", "alignment", _set("CONTRACT", "SCHEMA_CHANGED", True)),
    ("gate changed", "alignment", _set("CONTRACT", "GATE_CHANGED", True)),
    (
        "900 raised to fit V2",
        "alignment",
        _set("CONTRACT", "EVIDENCE_BOUND_REASONING_SUMMARY_MAX_LENGTH", 1200),
    ),
    ("1200 chosen because V2 returned 1113", "alignment", _set("PROPOSED_MAX_LENGTH", 1200)),
    ("V2's answer rescued", "alignment", _set("OPERATOR_DECISION", "V2_ANSWER_RESCUED", True)),
    (
        "V2's answer used to establish a maximum",
        "alignment",
        lambda d: d["V2_OUTPUT_USE"]["USED_TO_ESTABLISH"].append(
            "a maxLength of 1200 from V2's 1113 characters"
        ),
    ),
    (
        "V2's answer treated as a candidate",
        "alignment",
        lambda d: d["V2_OUTPUT_USE"]["USED_TO_ESTABLISH"].append(
            "a candidate Opportunity for human review"
        ),
    ),
    (
        "V2's use widened by a new key",
        "alignment",
        _set("V2_OUTPUT_USE", "USED_TO_CHOOSE", ["a new maxLength"]),
    ),
    (
        "V2's value used to choose a maximum",
        "alignment",
        _set("OPERATOR_DECISION", "V2_VALUE_USED_TO_CHOOSE_A_MAXIMUM", True),
    ),
    (
        "the decision read as inference approval",
        "alignment",
        _set("OPERATOR_DECISION", "AUTHORISES_AN_INFERENCE", True),
    ),
    ("the operator's words reworded", "alignment", _reword_statement),
    ("a V2 fact altered", "alignment", _set("V2_FACTS", "OUTPUT_TOKENS", 3000)),
    (
        "only the failed field audited",
        "alignment",
        _set("OTHER_SCHEMA_BOUNDS_MISSING_FROM_V1_1_0", []),
    ),
    (
        "no other bound missing",
        "alignment",
        _set("WERE_OTHER_SCHEMA_BOUNDS_MISSING_FROM_PROMPT", False),
    ),
    (
        "a narrative bound reclassified out of the prompt",
        "alignment",
        _row("subject", "maxLength", "class", INTERNAL_VALIDATOR_ONLY),
    ),
    (
        "v1.1.0 claimed to state the 900",
        "alignment",
        _row(SUMMARY, "maxLength", "explicit_in_v1_1_0", True),
    ),
    (
        "a bound claimed stated in v1.2.0 that is not",
        "alignment",
        _set("UNSTATED_IN_V1_2_0", ["subject maxLength"]),
    ),
    (
        "truncation permitted",
        "alignment",
        _set("ENFORCEMENT", "POST_PROCESSING", "TRUNCATION", True),
    ),
    (
        "auto-summary permitted",
        "alignment",
        _set("ENFORCEMENT", "POST_PROCESSING", "AUTO_SUMMARY", True),
    ),
    (
        "the validator demoted",
        "alignment",
        _set("ENFORCEMENT", "LOCAL_VALIDATOR_AUTHORITATIVE", False),
    ),
    ("a model call", "alignment", _set("ACCOUNTING", "MODEL_CALLS", 1)),
    ("a provider request", "alignment", _set("ACCOUNTING", "PROVIDER_REQUESTS", 1)),
    ("TED bytes", "alignment", _set("ACCOUNTING", "TED_BYTES_SENT", 3604)),
    ("a canonical mutation", "alignment", _set("ACCOUNTING", "CANONICAL_MUTATIONS", 1)),
    ("a drift count altered", "alignment", _set("DRIFT_PROPERTY", "A_MUTATIONS", 31)),
    (
        "the renderer renamed",
        "alignment",
        _set("RENDERER", "id", "output-constraint-renderer@9.9.9"),
    ),
    ("the prompt recorded as sent", "prompt", _set("SENT", True)),
    (
        "a prompt bound moved to 1200",
        "prompt",
        _replace_in_system("at most 900 characters", "at most 1200 characters"),
    ),
    (
        "the prompt still omitting the 900",
        "prompt",
        _replace_in_system(f"  {SUMMARY}\n    at most 900 characters\n\n", ""),
    ),
    ("the prompt version", "prompt", _set("PROMPT_VERSION", "1.1.0")),
    ("the predecessor digest", "prompt", _set("PREDECESSOR_PROMPT_SHA256", "0" * 64)),
    ("the trusted region moved", "prompt", _set("TRUSTED_CONTEXT_SHA256", "0" * 64)),
    ("the TED region moved", "prompt", _set("UNTRUSTED_SHA256", "0" * 64)),
    ("the representation moved", "prompt", _set("TED_REPRESENTATION_SHA256", "0" * 64)),
    (
        "research semantics changed",
        "prompt",
        _set("SEMANTIC_DIFF", "research_semantics_changed", True),
    ),
]


@pytest.mark.parametrize(("which", "fn"), [c[1:] for c in REFUSED], ids=[c[0] for c in REFUSED])
def test_a_violation_is_refused_through_the_whole_gate(world, which, fn) -> None:
    _edit(which, fn)
    with pytest.raises(GATE.ValidationError):
        GATE.validate()


def test_the_copies_validate_before_anything_is_edited(world) -> None:
    GATE.validate()


def test_a_note_rewording_binds_nothing(world) -> None:
    _edit("alignment", _set("drift_note", "Reworded; a note explains and binds nothing"))
    GATE.validate()


# ================================================================== gate 72, code-level


def _edited_copy(tmp_path: pathlib.Path, monkeypatch, name: str, fn) -> None:
    source = getattr(GATE, name)
    doc = _read(source)
    fn(doc)
    target = tmp_path / source.name
    target.write_text(json.dumps(doc, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    monkeypatch.setattr(GATE, name, target)


@pytest.mark.parametrize(
    ("name", "fn"),
    [
        ("RESPONSE_V2", _set("PERSISTED", "HUMAN_REVIEW_CANDIDATE")),
        ("RECORD_V2", _set("HUMAN_REVIEW_PACKET", "PRODUCED")),
        ("RECORD_V2", _set("OPPORTUNITY_PERSISTED", True)),
    ],
    ids=["the response marked a candidate", "a review packet produced", "an Opportunity persisted"],
)
def test_v2s_rejected_answer_is_never_a_candidate(world, monkeypatch, name, fn) -> None:
    _edited_copy(world, monkeypatch, name, fn)
    with pytest.raises(GATE.ValidationError, match="never a candidate"):
        GATE.validate()


def test_the_history_is_the_one_mission_1_84_7_left() -> None:
    GATE._check_history()


@pytest.mark.parametrize("name", sorted(GATE.HISTORY_SHA256))
def test_a_rewritten_historical_record_is_refused(tmp_path, monkeypatch, name) -> None:
    data = tmp_path / "data"
    data.mkdir()
    for each in GATE.HISTORY_SHA256:
        shutil.copyfile(GATE.DATA / each, data / each)
    monkeypatch.setattr(GATE, "DATA", data)
    GATE._check_history()
    (data / name).write_bytes((data / name).read_bytes() + b" ")
    with pytest.raises(GATE.ValidationError, match="never rewritten"):
        GATE._check_history()


def test_a_schema_bound_moved_under_an_unchanged_prompt_is_refused(monkeypatch) -> None:
    moved = copy.deepcopy(SCHEMA)
    moved["properties"][SUMMARY]["maxLength"] = 1200
    monkeypatch.setattr(GATE, "SECOND_OPPORTUNITY_OUTPUT_SCHEMA_V1_1", moved)
    with pytest.raises(GATE.ValidationError, match="not the rendering of the live schema"):
        GATE._check_composition()


def test_a_prompt_bound_moved_under_an_unchanged_schema_is_refused(monkeypatch) -> None:
    edited = SECOND_OPPORTUNITY_OUTPUT_CONSTRAINTS_V1_2.replace(
        "at most 900 characters", "at most 1200 characters"
    )
    assert edited != SECOND_OPPORTUNITY_OUTPUT_CONSTRAINTS_V1_2
    monkeypatch.setattr(GATE, "SECOND_OPPORTUNITY_OUTPUT_CONSTRAINTS_V1_2", edited)
    with pytest.raises(GATE.ValidationError, match="not the rendering"):
        GATE._check_composition()


def test_a_prompt_patched_only_for_the_failed_field_is_refused(world, monkeypatch) -> None:
    """Stating the 900 and nothing else is the tailored fix the operator refused."""
    patched = SECOND_OPPORTUNITY_SYSTEM_V1_1 + f"\n  {SUMMARY}\n    at most 900 characters\n"
    monkeypatch.setattr(GATE, "SECOND_OPPORTUNITY_SYSTEM_V1_2", patched)
    with pytest.raises(GATE.ValidationError):
        GATE._check_inventory(_read(GATE.ALIGNMENT))


def _source_with(tmp_path: pathlib.Path, source: pathlib.Path, old: str, new: str) -> pathlib.Path:
    text = source.read_text(encoding="utf-8")
    assert text.count(old) == 1, old
    target = tmp_path / source.name
    target.write_text(text.replace(old, new, 1), encoding="utf-8")
    return target


def test_a_block_written_by_hand_is_refused(tmp_path, monkeypatch) -> None:
    old = (
        "SECOND_OPPORTUNITY_OUTPUT_CONSTRAINTS_V1_2 = render_output_constraints(\n"
        "    SECOND_OPPORTUNITY_OUTPUT_SCHEMA_V1_1, OUTPUT_CONSTRAINT_NOTES_V1_2\n)"
    )
    new = 'SECOND_OPPORTUNITY_OUTPUT_CONSTRAINTS_V1_2 = "  written by hand\\n    at most so many"'
    monkeypatch.setattr(
        GATE, "CONTRACT_SOURCE", _source_with(tmp_path, GATE.CONTRACT_SOURCE, old, new)
    )
    with pytest.raises(GATE.ValidationError, match="not rendered from the live"):
        GATE._check_renderer()


def test_a_bound_hardcoded_beside_the_schema_is_refused(tmp_path, monkeypatch) -> None:
    old = 'SECOND_OPPORTUNITY_PROMPT_VERSION_V1_2 = "1.2.0"\n'
    new = old + "PROMPT_MAX_REASONING_LENGTH = 900\n"
    monkeypatch.setattr(
        GATE, "CONTRACT_SOURCE", _source_with(tmp_path, GATE.CONTRACT_SOURCE, old, new)
    )
    with pytest.raises(GATE.ValidationError, match="carries the number 900"):
        GATE._check_renderer()


def test_a_bound_written_into_the_renderer_is_refused(tmp_path, monkeypatch) -> None:
    old = '_ROOT = "<root>"\n'
    new = old + "_REASONING_MAX = 900\n"
    monkeypatch.setattr(
        GATE, "RENDERER_SOURCE", _source_with(tmp_path, GATE.RENDERER_SOURCE, old, new)
    )
    with pytest.raises(GATE.ValidationError, match="carries the number 900"):
        GATE._check_renderer()


def test_a_renderer_that_could_read_a_record_is_refused(tmp_path, monkeypatch) -> None:
    monkeypatch.setattr(
        GATE,
        "RENDERER_SOURCE",
        _source_with(tmp_path, GATE.RENDERER_SOURCE, "import re\n", "import json\nimport re\n"),
    )
    with pytest.raises(GATE.ValidationError, match="imports 'json'"):
        GATE._check_renderer()
