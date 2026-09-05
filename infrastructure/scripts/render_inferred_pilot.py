"""Render and validate the Mission 1.56 pilot artifacts, and hash the manifest.

Three documents, cross-checked against each other and against the repository:
the candidate selection, the reviewed semantic-equivalence decision, and the
write manifest the operator approves. `validate()` refuses a manifest whose
target key does not recompute from its own facts, whose threshold claims a
provenance the held data cannot support, or which records an evaluator result it
cannot yet have.

    uv run python infrastructure/scripts/render_inferred_pilot.py
    uv run python infrastructure/scripts/render_inferred_pilot.py --check
    uv run python infrastructure/scripts/render_inferred_pilot.py --hash

Every input is a repository file, so this is deterministic from an empty
database and safe in CI.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import pathlib

ROOT = pathlib.Path(__file__).resolve().parents[2]
DATA = ROOT / "docs" / "data"

SELECTION = DATA / "first-deterministic-inferred-pilot-candidate-selection-v1.json"
EQUIVALENCE = DATA / "first-deterministic-inferred-pilot-equivalence-v1.json"
MANIFEST = DATA / "first-deterministic-inferred-pilot-manifest-v1.json"
SUBJECT_REGISTRY = DATA / "canonical-subject-registry-v1.json"

# Written by `run_inferred_pilot.py` and `report_inferred_pilot_resolution.py`
# AFTER approval. Absent before the pilot runs, and rendered when present -- so
# this gate covers the whole mission at the end without failing in the middle of
# it.
EXECUTION = DATA / "first-deterministic-inferred-pilot-v1.json"
RESOLUTION = DATA / "first-deterministic-inferred-pilot-resolution-v1.json"

RENDERED = {
    SELECTION: DATA / "first-deterministic-inferred-pilot-candidate-selection-v1.md",
    EQUIVALENCE: DATA / "first-deterministic-inferred-pilot-equivalence-v1.md",
    MANIFEST: DATA / "first-deterministic-inferred-pilot-manifest-v1.md",
    EXECUTION: DATA / "first-deterministic-inferred-pilot-v1.md",
    RESOLUTION: DATA / "first-deterministic-inferred-pilot-resolution-v1.md",
}

# A threshold recorded today against data held since Mission 1.19 can never
# satisfy `recorded_at < retrieved_at`.
FORBIDDEN_PROVENANCE = "PREREGISTERED"
EQUIVALENCE_DIMENSIONS = (
    "CANONICAL_SUBJECT",
    "METRIC_DEFINITION",
    "TIME_BOUND",
    "POPULATION",
    "GEOGRAPHY",
    "UNIT",
    "ADJUSTMENT",
    "METHODOLOGY_SEMANTICS",
)
REFUSAL_RESULTS = {"NOT_APPLICABLE", "UNKNOWN"}
DIRECTIONAL_RESULTS = {"SUPPORTS", "CONTRADICTS"}


class ValidationError(Exception):
    """A pilot artifact claims something the repository does not support."""


def canonical_json(payload: object) -> str:
    """The same canonicalisation `sros_claim_model` uses for a proposition key:
    sorted keys, no incidental whitespace, stable separators."""
    return json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def manifest_hash(manifest: dict) -> str:
    return hashlib.sha256(canonical_json(manifest).encode("utf-8")).hexdigest()


def _proposition_key(facts: dict) -> str:
    """Recomputed through the REAL claim-model, so the manifest's key is
    verified rather than trusted. Imported lazily so `--check` still works in an
    environment where only the docs are present."""
    from sros_claim_model import proposition_key

    return proposition_key(facts)


def validate() -> tuple[dict, dict, dict]:  # noqa: C901
    for path in (SELECTION, EQUIVALENCE, MANIFEST):
        if not path.exists():
            raise ValidationError(f"{path.name} does not exist")
    selection = json.loads(SELECTION.read_text(encoding="utf-8"))
    equivalence = json.loads(EQUIVALENCE.read_text(encoding="utf-8"))
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))

    # ------------------------------------------------ the evaluator has not run
    if manifest.get("evaluator_has_not_run") is not True:
        raise ValidationError("the manifest must assert that no evaluation exists yet")
    for banned in ("evaluation_result", "outcome", "result"):
        if banned in manifest:
            raise ValidationError(
                f"the manifest carries `{banned}`. §14 forbids it: a manifest that already knew "
                "the answer would be a manifest written around it"
            )

    # --------------------------------------------------------- one candidate
    chosen = selection["selected"]["signal_id"]
    if selection["selection_within_the_passing_family"]["selected_signal_id"] != chosen:
        raise ValidationError("the selection artifact disagrees with itself about the candidate")
    if manifest["selected_signal"]["signal_id"] != chosen:
        raise ValidationError("the manifest and the selection name different Signals")
    if equivalence["measurement"]["signal_id"] != chosen:
        raise ValidationError("the equivalence decision is about a different Signal")

    if selection["magnitude_was_not_a_selection_criterion"].get("asserted") is not True:
        raise ValidationError("§5 forbids selecting on magnitude, and the record must say so")
    for banned in ("measurement magnitude", "expected evaluator direction"):
        if banned not in selection["magnitude_was_not_a_selection_criterion"]["not_used"]:
            raise ValidationError(f"the record does not exclude {banned!r} as a criterion")

    # -------------------------------------------------- every family accounted
    inspected = sum(family["count"] for family in selection["families"])
    if inspected != selection["signals_inspected"]:
        raise ValidationError(
            f"the families account for {inspected} Signals and the record claims "
            f"{selection['signals_inspected']}"
        )
    passing = [f for f in selection["families"] if f["verdict"] == "PASSES"]
    if len(passing) != selection["families_passing"]:
        raise ValidationError("the passing-family count disagrees with the family verdicts")
    for family in selection["families"]:
        if family["verdict"] == "FAILS" and not (
            family.get("failed_gate") or family.get("failed_gates")
        ):
            raise ValidationError(f"{family['signal_type_id']} fails no named gate")
    if len(selection["hard_gates_for_the_selected_candidate"]) != 15:
        raise ValidationError("§4 lists fifteen hard gates and each needs a verdict")
    for gate in selection["hard_gates_for_the_selected_candidate"]:
        if gate["met"] is not True:
            raise ValidationError(f"gate {gate['n']} is not met, so no candidate may be selected")
        if not gate.get("how", "").strip():
            raise ValidationError(f"gate {gate['n']} is met by nothing stated")

    # ------------------------------------------------------- held-data use
    use = selection["held_data_analytical_use"]
    if use.get("established") is not True:
        raise ValidationError("§42: held-data analytical use must be established, not assumed")
    if not use.get("new_collection_is_a_different_question", "").strip():
        raise ValidationError(
            "the record must keep acquisition eligibility and held-data use apart"
        )

    # ------------------------------------------------------- the subject exists
    registry = json.loads(SUBJECT_REGISTRY.read_text(encoding="utf-8"))
    subjects = {entry["subject_id"] for entry in registry["subjects"]}
    subject = manifest["target_proposition"]["facts"]["canonical_subject_id"]
    if subject not in subjects:
        raise ValidationError(
            f"the target names canonical subject {subject!r}, which the reviewed registry does "
            "not contain. A subject invented for a pilot is a subject nobody reviewed"
        )

    # --------------------------------------------------------- the target key
    facts = manifest["target_proposition"]["facts"]
    recomputed = _proposition_key(facts)
    if recomputed != manifest["target_proposition"]["proposition_key"]:
        raise ValidationError(
            f"the manifest's proposition key does not recompute from its own facts "
            f"({recomputed} != {manifest['target_proposition']['proposition_key']})"
        )
    for absent in ("source_id", "measurement_value", "direction", "signal_id"):
        if absent in facts:
            raise ValidationError(f"the target proposition carries {absent!r}; ADR-036 excludes it")
    if facts.get("claim_type") != "INFERRED":
        raise ValidationError("the target is an INFERRED proposition")

    # ------------------------------------------------------------- threshold
    threshold = manifest["threshold_registration"]
    if threshold["provenance_status"] == FORBIDDEN_PROVENANCE:
        raise ValidationError(
            "a threshold recorded today against already-held data cannot be PREREGISTERED: that "
            "would assert this system did not hold the measurement when the bound was frozen"
        )
    if threshold["provenance_status"] not in (
        "SOURCE_NATIVE",
        "EXTERNAL_NORM",
        "POST_HOC",
        "UNKNOWN",
    ):
        raise ValidationError(f"unknown threshold provenance {threshold['provenance_status']!r}")
    if threshold["provenance_status"] == "UNKNOWN":
        raise ValidationError(
            "§7 forbids UNKNOWN where the origin is established; an operator chose this bound today"
        )
    if threshold.get("preregistered_was_attempted") is not False:
        raise ValidationError("the record must state that PREREGISTERED was not attempted")
    if not threshold.get("why_preregistered_was_not_attempted", "").strip():
        raise ValidationError("and why")
    if (
        threshold["provenance_status"] == "POST_HOC"
        and threshold.get("calibration_eligible") is not False
    ):
        raise ValidationError("a POST_HOC bound is never calibration-eligible")
    impossible = threshold.get("preregistration_is_arithmetically_impossible", {})
    retrieved = impossible.get("measurement_retrieved_at", "")
    if retrieved != manifest["selected_signal"].get("retrieved_at"):
        raise ValidationError(
            "the threshold's preregistration arithmetic must cite the SAME retrieval instant "
            "the selected Signal records, or it is arithmetic about a different measurement"
        )
    if not retrieved.startswith("2026-") or retrieved >= f"{manifest['recorded_at']}T":
        raise ValidationError(
            f"the measurement was retrieved at {retrieved!r}, which is not before the day this "
            "manifest was written. If that were true, PREREGISTERED would be available and "
            "recording POST_HOC would be understating what this system can honestly claim"
        )
    if not threshold.get("the_disclosure_that_matters", "").strip():
        raise ValidationError(
            "the manifest must disclose whether the measurement was visible when the bound was "
            "chosen; for held data it always was, and hiding it would be the outcome-chasing §10 "
            "exists to prevent"
        )
    for field in ("threshold_operator", "threshold_value", "unit", "scope_subject_id"):
        if (
            threshold[field]
            != facts[{"scope_subject_id": "canonical_subject_id"}.get(field, field)]
        ):
            raise ValidationError(f"the threshold's {field} disagrees with the target proposition")

    # ------------------------------------------------------------ equivalence
    if manifest["semantic_equivalence"]["basis_id"] != equivalence["basis_id"]:
        raise ValidationError("the manifest and the equivalence artifact name different bases")
    checked = tuple(entry["dimension"] for entry in equivalence["dimensions"])
    if checked != EQUIVALENCE_DIMENSIONS:
        raise ValidationError(
            f"the eight frozen dimensions must all be checked, in order: {checked}"
        )
    for entry in equivalence["dimensions"]:
        if entry["checked"] is not True or not entry.get("finding", "").strip():
            raise ValidationError(f"dimension {entry['dimension']} has no finding")
    if equivalence["verdict"] == "EQUIVALENT":
        confidence = equivalence["interpretation_confidence"]
        if not isinstance(confidence.get("proposed_value"), (int, float)):
            raise ValidationError("an EQUIVALENT verdict must carry an interpretation confidence")
        if confidence["proposed_value"] == 1.0:
            raise ValidationError("ADR-037 §17 forbids 1.0 merely because the arithmetic is exact")
        if not 0.0 < confidence["proposed_value"] < 1.0:
            raise ValidationError("interpretation confidence is a unit-interval value")
        if confidence.get("not_invented_by_the_evaluator") is not True:
            raise ValidationError("the confidence must come from the reviewed basis")
        if (
            manifest["semantic_equivalence"]["interpretation_confidence"]
            != confidence["proposed_value"]
        ):
            raise ValidationError("the manifest and the basis disagree on the confidence")
    if (
        equivalence.get("model_calls") != 0
        or equivalence.get("no_model_generated_approval") is not True
    ):
        raise ValidationError("§44: the equivalence decision is documentary, never model-generated")
    if not equivalence.get("stated_limitations"):
        raise ValidationError("a reviewed basis states what bounds it")

    # ---------------------------------------------------------------- envelope
    envelope = manifest["canonical_mutation_envelope"]
    if envelope["threshold_registrations"] != 1:
        raise ValidationError("exactly one threshold registration is authorised")
    directional = envelope["directional_maximum"]
    refusal = envelope["refusal_maximum"]
    if directional != {
        "claims": 1,
        "claim_revisions": 1,
        "evidence": 1,
        "claim_derivations": 1,
        "proposition_evaluation_refusals": 0,
    }:
        raise ValidationError("the directional envelope is not the one §38 fixes")
    if refusal != {
        "claims": 0,
        "claim_revisions": 0,
        "evidence": 0,
        "claim_derivations": 0,
        "proposition_evaluation_refusals": 1,
    }:
        raise ValidationError("the refusal envelope is not the one §38 fixes")

    paths = {
        tuple(sorted(entry["if_result"])): entry["path"]
        for entry in manifest["allowed_persistence_paths"]
    }
    if paths.get(tuple(sorted(DIRECTIONAL_RESULTS))) != "DIRECTIONAL":
        raise ValidationError("SUPPORTS and CONTRADICTS route directionally")
    if paths.get(tuple(sorted(REFUSAL_RESULTS))) != "REFUSAL":
        raise ValidationError("NOT_APPLICABLE and UNKNOWN route to the refusal path")
    if manifest.get("all_four_results_are_legitimate") is not True:
        raise ValidationError("§22: all four evaluator results are legitimate pilot outcomes")
    if manifest.get("success_is_not_defined_as_supports") is not True:
        raise ValidationError("§1: the pilot must not be optimised for SUPPORTS")

    # ------------------------------------------------- the limitation is stated
    for artifact, key in (
        (selection, "the_limitation_worth_stating_before_approval"),
        (manifest, "known_limitation_the_operator_should_weigh"),
    ):
        block = artifact.get(key, {})
        if not block.get("detail", "").strip():
            raise ValidationError(f"{key} must state the limitation rather than name it")

    # The manifest's status never changes, and that is not an oversight. Marking
    # it APPROVED after the fact would change its bytes and therefore its hash,
    # and a frozen document that no longer answers to the hash it was frozen at
    # is not frozen. The approval lives in the execution record instead.
    if manifest.get("status") != "AWAITING_OPERATOR_APPROVAL":
        raise ValidationError(
            f"the manifest's status reads {manifest.get('status')!r}. A manifest is frozen at "
            "the hash the operator approved, so editing it afterwards -- even to record that "
            "it was approved -- destroys the only thing the approval names"
        )

    _validate_execution(manifest)
    return selection, equivalence, manifest


def _validate_execution(manifest: dict) -> None:
    """The execution record, once it exists.

    The load-bearing check is the first one: the hash the run recorded must
    still be the hash of the manifest on disk. If a later edit moves the
    manifest, this gate goes red rather than leaving a record that says
    "approved" beside a document nobody approved.
    """
    if not EXECUTION.exists():
        return
    execution = json.loads(EXECUTION.read_text(encoding="utf-8"))

    if execution["approval"]["manifest_sha256"] != manifest_hash(manifest):
        raise ValidationError(
            "the execution record names a manifest hash the manifest no longer has. Either "
            "the manifest was edited after it was approved, or this record describes a "
            "different run"
        )
    if execution.get("status") != "EXECUTED":
        raise ValidationError(f"unexpected execution status {execution.get('status')!r}")

    result = execution["evaluation"]["result"]
    routed = {
        r: entry["path"]
        for entry in manifest["allowed_persistence_paths"]
        for r in entry["if_result"]
    }
    if result not in routed:
        raise ValidationError(f"{result!r} is not one of the four results the manifest routes")
    if execution["persistence"]["path"] != routed[result]:
        raise ValidationError(
            f"a {result} evaluation took the {execution['persistence']['path']} path, and the "
            f"manifest routes it to {routed[result]}"
        )
    if execution["evaluation"]["calls"] != 1:
        raise ValidationError("§9 authorises one evaluation, not several")
    if execution["evaluation"]["model_calls"] != 0:
        raise ValidationError("a deterministic evaluation calls no model")
    if (
        execution["evaluation"]["proposition_key"]
        != manifest["target_proposition"]["proposition_key"]
    ):
        raise ValidationError("the run evaluated a different proposition from the approved one")

    # The envelope, re-checked against the recorded counters rather than against
    # the database, so this stays a repository gate that CI can run.
    envelope = manifest["canonical_mutation_envelope"]
    allowed = dict(
        envelope["directional_maximum"]
        if execution["persistence"]["path"] == "DIRECTIONAL"
        else envelope["refusal_maximum"]
    )
    allowed["threshold_registrations"] = envelope["threshold_registrations"]
    before, after = execution["counters"]["before"], execution["counters"]["after"]
    for name in before:
        moved = after[name] - before[name]
        if moved != allowed.get(name, 0):
            raise ValidationError(
                f"PILOT_MUTATION_ENVELOPE_VIOLATION: {name} moved by {moved}, and the manifest "
                f"authorises {allowed.get(name, 0)}"
            )
    if execution["counters"]["after_replay"] != after:
        raise ValidationError("the recorded replay changed the counters, so it was not a replay")
    if execution["replay"]["rows_created"] != 0:
        raise ValidationError("a replay that created rows is not idempotent")

    if RESOLUTION.exists():
        resolution = json.loads(RESOLUTION.read_text(encoding="utf-8"))
        if resolution["claim_id"] != execution["persistence"]["claim_id"]:
            raise ValidationError("the resolution report is about a different Claim")
        if resolution.get("rows_written") != 0 or resolution.get("read_only") is not True:
            raise ValidationError("the resolution report is read-only, or it is not a report")


def _row(cells: list[str]) -> str:
    return "| " + " | ".join(cells) + " |"


def render_selection(record: dict) -> str:
    lines: list[str] = []
    add = lines.append
    add("# First Deterministic Inferred Pilot — Candidate Selection V1")
    add("")
    add(f"**Mission {record['mission']} — recorded {record['recorded_at']}.**")
    add("")
    add("> **This document is GENERATED.** Edit the JSON and re-run")
    add("> `infrastructure/scripts/render_inferred_pilot.py`.")
    add("")
    add(record["method"])
    add("")
    add(
        f"**{record['signals_inspected']} Signals inspected across "
        f"{record['families_inspected']} families. {record['families_passing']} family passes, "
        f"{record['signals_passing']} Signals.**"
    )
    add("")
    add(_row(["family", "n", "unit state", "verdict", "why"]))
    add(_row(["---", "---", "---", "---", "---"]))
    for family in record["families"]:
        gate = family.get("failed_gate") or family.get("failed_gates")
        verdict = family["verdict"] if family["verdict"] == "PASSES" else f"FAILS gate {gate}"
        add(
            _row(
                [
                    f"`{family['signal_type_id']}`",
                    str(family["count"]),
                    family["unit_state"],
                    f"**{verdict}**",
                    family["why"],
                ]
            )
        )
    add("")
    for family in record["families"]:
        for extra in ("note", "note_this_is_the_painful_one", "second_concern"):
            if extra in family:
                add(f"*{family['signal_type_id']} — {family[extra]}*")
                add("")

    add("## Selection within the passing family")
    add("")
    within = record["selection_within_the_passing_family"]
    add(within["outcome"])
    add("")
    add(f"Tie-break: {within['tie_break']}. Selected `{within['selected_signal_id']}`.")
    add("")
    magnitude = record["magnitude_was_not_a_selection_criterion"]
    add(f"**The magnitude was not a criterion.** {magnitude['how_it_is_checkable']}")
    add("")
    add(f"*{magnitude['what_was_read_afterwards']}*")
    add("")

    add("## The selected candidate")
    add("")
    selected = record["selected"]
    for key in (
        "signal_id",
        "source_id",
        "record_kind_id",
        "signal_type_id",
        "magnitude",
        "magnitude_unit",
        "period_labels",
        "content_id",
        "content_platform",
        "audience_class",
        "access_channel",
    ):
        add(f"- `{key}`: {selected[key]}")
    add("")

    add("## The fifteen hard gates")
    add("")
    add(_row(["", "gate", "how"]))
    add(_row(["---", "---", "---"]))
    for gate in record["hard_gates_for_the_selected_candidate"]:
        add(_row([str(gate["n"]), gate["gate"], gate["how"]]))
    add("")

    add("## Held-data analytical use")
    add("")
    use = record["held_data_analytical_use"]
    add(f"**{use['question']}**")
    add("")
    add(use["basis"])
    add("")
    add(use["licence"])
    add("")
    add(f"*{use['new_collection_is_a_different_question']}*")
    add("")

    add("## The limitation, stated before approval")
    add("")
    limitation = record["the_limitation_worth_stating_before_approval"]
    add(f"**`{limitation['concern']}`.** {limitation['detail']}")
    add("")
    add(limitation["why_it_is_still_a_legitimate_INFERRED_proposition"])
    add("")
    add(f"*Where the measurer does enter.* {limitation['where_the_measurer_does_enter']}")
    add("")
    add(f"*{limitation['the_family_that_would_have_been_better']}*")
    add("")
    return "\n".join(lines) + "\n"


def render_equivalence(record: dict) -> str:
    lines: list[str] = []
    add = lines.append
    add("# First Deterministic Inferred Pilot — Semantic Equivalence V1")
    add("")
    add(
        f"**Mission {record['mission']} — basis `{record['basis_id']}`, recorded {record['recorded_at']}.**"
    )
    add("")
    add("> **This document is GENERATED.** Edit the JSON and re-run")
    add("> `infrastructure/scripts/render_inferred_pilot.py`.")
    add("")
    add(record["what_this_decides"])
    add("")
    add(
        f"Network requests **{record['network_requests']}**, model calls "
        f"**{record['model_calls']}**, every document already held "
        f"**{record['every_document_cited_is_already_held']}**."
    )
    add("")
    add("## Documents relied on")
    add("")
    add(_row(["document", "held since", "establishes"]))
    add(_row(["---", "---", "---"]))
    for document in record["documents_relied_on"]:
        add(_row([document["document"], document["held_since"], document["what_it_establishes"]]))
    add("")
    add("## The eight dimensions")
    add("")
    add(_row(["dimension", "finding"]))
    add(_row(["---", "---"]))
    for entry in record["dimensions"]:
        add(_row([f"`{entry['dimension']}`", entry["finding"]]))
    add("")
    add(f"## Verdict — `{record['verdict']}`")
    add("")
    add(record["why"])
    add("")
    confidence = record["interpretation_confidence"]
    add(f"### Interpretation confidence — {confidence['proposed_value']}")
    add("")
    add(confidence["means"])
    add("")
    add(f"**Why not 1.0.** {confidence['why_not_1_0']}")
    add("")
    add(f"**Why not lower.** {confidence['why_not_lower']}")
    add("")
    add(f"*Decided by: {confidence['decided_by']}.*")
    add("")
    add("## Stated limitations")
    add("")
    for limitation in record["stated_limitations"]:
        add(f"- {limitation}")
    add("")
    add(f"Reviewed by **{record['reviewed_by']}**, {record['review_mechanism']}.")
    add("")
    return "\n".join(lines) + "\n"


def render_manifest(record: dict, digest: str) -> str:
    lines: list[str] = []
    add = lines.append
    add("# First Deterministic Inferred Pilot — Write Manifest V1")
    add("")
    add(
        f"**Mission {record['mission']} — recorded {record['recorded_at']}. Status: {record['status']}.**"
    )
    add("")
    add("> **This document is GENERATED.** Edit the JSON and re-run")
    add("> `infrastructure/scripts/render_inferred_pilot.py`.")
    add("")
    add(f"**SHA-256 `{digest}`**")
    add("")
    add(record["what_this_authorises"])
    add("")
    add(f"*{record['no_evaluator_result_is_recorded_here']}*")
    add("")

    add("## The target proposition")
    add("")
    target = record["target_proposition"]
    add(f"> {target['reads_as']}")
    add("")
    add(_row(["fact", "value"]))
    add(_row(["---", "---"]))
    for key, value in target["facts"].items():
        add(_row([f"`{key}`", f"`{value}`"]))
    add("")
    add(f"Key `{target['proposition_key']}`, recomputed from these facts by the validator.")
    add("")
    add("Carries no " + ", ".join(f"`{f}`" for f in target["carries_no"]) + ".")
    add("")

    add("## The Signal")
    add("")
    signal = record["selected_signal"]
    for key in (
        "signal_id",
        "source_id",
        "measurement_value",
        "unit",
        "period_labels",
        "content_id",
        "audience_class",
    ):
        add(f"- `{key}`: {signal[key]}")
    add("")
    add(f"*{signal['selected_by']}*")
    add("")

    add("## The threshold registration")
    add("")
    threshold = record["threshold_registration"]
    add(
        f"`{threshold['threshold_operator']} {threshold['threshold_value']} "
        f"{threshold['unit']}`, provenance **{threshold['provenance_status']}**, recorded by "
        f"`{threshold['recorded_by']}`."
    )
    add("")
    add(f"**Why POST_HOC.** {threshold['why_post_hoc']}")
    add("")
    add(
        f"PREREGISTERED attempted: **{threshold['preregistered_was_attempted']}**. "
        f"{threshold['why_preregistered_was_not_attempted']}"
    )
    add("")
    add(f"- SOURCE_NATIVE: {threshold['source_native_considered']}")
    add(f"- EXTERNAL_NORM: {threshold['external_norm_considered']}")
    add(f"- UNKNOWN: {threshold['unknown_considered']}")
    add("")
    add(f"**The disclosure that matters.** {threshold['the_disclosure_that_matters']}")
    add("")
    impossible = threshold["preregistration_is_arithmetically_impossible"]
    add("### PREREGISTERED is not merely unavailable, it is arithmetically impossible")
    add("")
    add(impossible["rule"])
    add("")
    add(f"- measurement retrieved at `{impossible['measurement_retrieved_at']}`")
    add(f"- threshold recordable no earlier than {impossible['threshold_recorded_at_earliest']}")
    add("")
    add(impossible["consequence"])
    add("")
    add(
        f"Calibration eligible **{threshold['calibration_eligible']}**. "
        f"{threshold['calibration_eligibility_is_not_truth']}"
    )
    add("")

    add("## Equivalence")
    add("")
    equivalence = record["semantic_equivalence"]
    add(
        f"Basis `{equivalence['basis_id']}`, verdict **{equivalence['verdict']}**, "
        f"{equivalence['dimensions_checked']} dimensions, interpretation confidence "
        f"**{equivalence['interpretation_confidence']}**, reviewed by "
        f"`{equivalence['reviewed_by']}`."
    )
    add("")

    add("## Allowed persistence paths")
    add("")
    add(_row(["if the evaluator returns", "path", "writes"]))
    add(_row(["---", "---", "---"]))
    for entry in record["allowed_persistence_paths"]:
        add(
            _row(
                [
                    ", ".join(f"`{r}`" for r in entry["if_result"]),
                    f"**{entry['path']}**",
                    ", ".join(f"`{t}`" for t in entry["writes"]),
                ]
            )
        )
    add("")
    add("**All four results are legitimate. Success is not defined as SUPPORTS.**")
    add("")

    add("## Canonical mutation envelope")
    add("")
    envelope = record["canonical_mutation_envelope"]
    add(
        f"`threshold_registrations` **+{envelope['threshold_registrations']}**, then exactly one of:"
    )
    add("")
    add(_row(["counter", "directional max", "refusal max"]))
    add(_row(["---", "---", "---"]))
    for counter in envelope["directional_maximum"]:
        add(
            _row(
                [
                    f"`{counter}`",
                    f"+{envelope['directional_maximum'][counter]}",
                    f"+{envelope['refusal_maximum'][counter]}",
                ]
            )
        )
    add("")
    add(
        f"Every other counter: **{envelope['every_other_counter']}**. On violation: "
        f"`{envelope['on_violation']}`."
    )
    add("")

    add("## What this pilot will not do")
    add("")
    for item in record["what_this_pilot_will_not_do"]:
        add(f"- {item}")
    add("")

    add("## The limitation the operator should weigh")
    add("")
    limitation = record["known_limitation_the_operator_should_weigh"]
    add(f"**`{limitation['flag']}`.** {limitation['detail']}")
    add("")
    add(limitation["the_better_family_and_why_it_was_excluded"])
    add("")

    add("## Approval")
    add("")
    approval = record["approval"]
    add(f"    APPROVE MISSION 1.56 PILOT {digest}")
    add("")
    add(f"Until approved: {approval['until_approved']}.")
    add("")
    return "\n".join(lines) + "\n"


def render_execution(record: dict) -> str:
    lines: list[str] = []
    add = lines.append
    add("# First Deterministic Inferred Pilot — Execution Record V1")
    add("")
    add(
        f"**Mission {record['mission']} — executed {record['recorded_at']}. Status: {record['status']}.**"
    )
    add("")
    add("> **This document is GENERATED.** Edit the JSON and re-run")
    add("> `infrastructure/scripts/render_inferred_pilot.py`.")
    add("")

    approval = record["approval"]
    add("## Approval")
    add("")
    add(
        f"Manifest SHA-256 `{approval['manifest_sha256']}`, approved by `{approval['approved_by']}`."
    )
    add("")
    add(approval["the_hash_is_the_approval"])
    add("")
    add(f"*{approval['the_manifest_was_not_edited_afterwards']}*")
    add("")

    evaluation = record["evaluation"]
    add(f"## The evaluator returned `{evaluation['result']}`")
    add("")
    add(f"> {evaluation['rationale']}")
    add("")
    add(
        f"Refusal reason **{evaluation['refusal_reason']}**, calibration eligible "
        f"**{evaluation['calibration_eligible']}**, evaluations **{evaluation['calls']}**, "
        f"re-runs with adjusted inputs **{evaluation['second_call_with_adjusted_inputs']}**, "
        f"model calls **{evaluation['model_calls']}**, network requests "
        f"**{evaluation['network_requests']}**."
    )
    add("")
    add(f"Proposition key `{evaluation['proposition_key']}`.")
    add("")

    threshold = record["threshold_registration"]
    add("## The bound")
    add("")
    add(
        f"`{threshold['registration_id']}`, provenance **{threshold['provenance_status']}**, "
        f"recorded {threshold['recorded_at']} by `{threshold['recorded_by']}`, created by this "
        f"run **{threshold['created_by_this_run']}**."
    )
    add("")
    add(threshold["written_before_the_evaluation"])
    add("")

    add("## What was written")
    add("")
    persistence = record["persistence"]
    add(_row(["", "value"]))
    add(_row(["---", "---"]))
    for key, value in persistence.items():
        add(_row([f"`{key}`", f"`{value}`"]))
    add("")

    add("## The replay")
    add("")
    replay = record["replay"]
    add(f"Status **{replay['status']}**, rows created **{replay['rows_created']}**.")
    add("")
    add(replay["what_it_proves"])
    add("")

    add("## Counters")
    add("")
    counters = record["counters"]
    add(_row(["counter", "before", "after", "after replay"]))
    add(_row(["---", "---", "---", "---"]))
    for name in counters["before"]:
        add(
            _row(
                [
                    f"`{name}`",
                    str(counters["before"][name]),
                    str(counters["after"][name]),
                    str(counters["after_replay"][name]),
                ]
            )
        )
    add("")
    add(
        f"INFERRED Claims **{counters['inferred_claims_before']} -> "
        f"{counters['inferred_claims_after']}**."
    )
    add("")

    add("## What this run did not do")
    add("")
    for item in record["what_this_run_did_not_do"]:
        add(f"- {item}")
    add("")

    add("## The limitation, restated after the fact")
    add("")
    limitation = record["known_limitation"]
    add(f"**`{limitation['flag']}`.** {limitation['detail']}")
    add("")
    return "\n".join(lines) + "\n"


def render_resolution(record: dict) -> str:
    lines: list[str] = []
    add = lines.append
    add("# First Deterministic Inferred Pilot — Downstream Resolution V1")
    add("")
    add(
        f"**Mission {record['mission']} — recorded {record['recorded_at']}. Rows written: {record['rows_written']}.**"
    )
    add("")
    add("> **This document is GENERATED.** Edit the JSON and re-run")
    add("> `infrastructure/scripts/render_inferred_pilot.py`.")
    add("")
    add(f"Claim `{record['claim_id']}`.")
    add("")

    add("## The reliability scope")
    add("")
    for key, value in record["scope"].items():
        add(f"- `{key}`: {value}")
    add("")

    reliability = record["reliability"]
    add(f"## Reliability — `{reliability['outcome']}`")
    add("")
    add(
        f"{reliability['candidates_offered']} current assessments offered, resolved value "
        f"**{reliability['reliability']}**."
    )
    add("")
    add(_row(["assessment", "value", "fields shared", "differs on"]))
    add(_row(["---", "---", "---", "---"]))
    for entry in reliability["nothing_leaked"]:
        add(
            _row(
                [
                    f"`{entry['assessment_id'][:8]}`",
                    str(entry["reliability"]),
                    f"{entry['fields_shared']} of 5",
                    ", ".join(f"`{f}`" for f in entry["differs_on"]),
                ]
            )
        )
    add("")
    add(reliability["why_it_matters"])
    add("")

    aggregation = record["aggregation"]
    add(f"## Aggregation — `{aggregation['status']}`")
    add("")
    add(
        f"Profile `{aggregation['profile']}` ({aggregation['calibration_state']}), raw "
        f"{aggregation['raw_evidence_count']}, scorable "
        f"{aggregation['scorable_evidence_count']}, non-scorable "
        f"{aggregation['non_scorable_evidence_count']}, support groups "
        f"{aggregation['support_group_count']}, contradiction groups "
        f"{aggregation['contradiction_group_count']}, level "
        f"{aggregation['evidence_level']}, score {aggregation['evidence_score']}."
    )
    add("")
    for requirement in aggregation["missing_requirements"]:
        add(f"- missing: {requirement}")
    add("")
    add(record["why_no_score_is_the_right_answer"])
    add("")

    direction = record["the_direction_that_had_never_existed"]
    add("## The direction that had never existed")
    add("")
    add(_row(["direction", "rows"]))
    add(_row(["---", "---"]))
    for name, count in sorted(direction["evidence_by_direction"].items()):
        add(_row([f"`{name}`", str(count)]))
    add("")
    add(
        f"Claims carrying a contradiction: **{direction['claims_carrying_a_contradiction']}**. "
        f"Claims carrying BOTH directions: **{direction['claims_carrying_both_directions']}**."
    )
    add("")
    add(f"**What this settles.** {direction['what_this_settles']}")
    add("")
    add(f"**What it does NOT settle.** {direction['what_this_does_NOT_settle']}")
    add("")
    return "\n".join(lines) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true")
    parser.add_argument("--hash", action="store_true")
    args = parser.parse_args()

    try:
        selection, equivalence, manifest = validate()
    except ValidationError as error:
        print(f"REFUSED  pilot artifacts: {error}")
        return 1

    digest = manifest_hash(manifest)
    if args.hash:
        print(digest)
        return 0

    rendered = {
        RENDERED[SELECTION]: render_selection(selection),
        RENDERED[EQUIVALENCE]: render_equivalence(equivalence),
        RENDERED[MANIFEST]: render_manifest(manifest, digest),
    }
    # Present only after the pilot has run. Rendered when present rather than
    # required, so this gate is green both before approval and after execution.
    for source, renderer in ((EXECUTION, render_execution), (RESOLUTION, render_resolution)):
        if source.exists():
            rendered[RENDERED[source]] = renderer(json.loads(source.read_text(encoding="utf-8")))

    if args.check:
        for path, text in rendered.items():
            if not path.exists():
                print(f"DRIFT    {path.name} does not exist")
                return 1
            if path.read_text(encoding="utf-8") != text:
                print(f"DRIFT    {path.name} does not match its record")
                return 1
        print(
            f"ok       {len(rendered)} pilot documents match their records; "
            f"manifest {digest[:16]}..."
        )
        return 0

    for path, text in rendered.items():
        path.write_text(text, encoding="utf-8", newline="\n")
        print(f"wrote    {path.name} ({len(text.splitlines())} lines)")
    print(f"manifest SHA-256 {digest}")
    print(f"status   {manifest['status']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
