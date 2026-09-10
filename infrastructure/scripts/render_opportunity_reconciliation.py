"""Render and validate the Opportunity reliability reconciliation (Mission 1.78).

Two records: the reconciliation (measured from the deployment by
`reconcile_opportunity_reliability.py`) and the current preparation v2 (produced by the
canonical runner through the late-resolution path). This gate holds them to each other, to
the historical v1 record, and to the parked apparatus arc, and refuses:

    HISTORY REWRITTEN. Revision 1 differing in any field after reconciliation; the v1
    preparation record's hash or its historical census moved; the stale sentence removed
    from revision 1's copy.

    THE HYPOTHESIS STRENGTHENED. Any of the seven carried fields differing between revision
    1 and revision 2; a model version on revision 2; a new Opportunity id.

    THE EVIDENCE SET WIDENED. Revision 2 citing anything revision 1 did not, or dropping
    anything it did; a row scorable without a resolved binding or non-scorable with one; a
    reliability that is not its bound assessment's; a value on a row whose scope no
    assessment covers.

    THE LIMITATION WRONG EITHER WAY. The stale sentence surviving into revision 2; a sentence
    Mission 1.77 did not touch dropped; counts in the new sentence disagreeing with the
    links; UNCALIBRATED, no score, no ranking absent from it.

    ANYTHING ELSE MOVED. A score table, an independence group, a non-Opportunity counter, a
    Q1 or Globalping record.

    uv run python infrastructure/scripts/render_opportunity_reconciliation.py
    uv run python infrastructure/scripts/render_opportunity_reconciliation.py --check

Deterministic from repository files, so it is safe in CI.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import pathlib

ROOT = pathlib.Path(__file__).resolve().parents[2]
DATA = ROOT / "docs" / "data"

RECONCILIATION = DATA / "opportunity-reliability-reconciliation-v1.json"
PREPARATION_V1 = DATA / "opportunity-preparation-v1.json"
PREPARATION_V2 = DATA / "opportunity-preparation-v2.json"
RENDERED_RECONCILIATION = DATA / "opportunity-reliability-reconciliation-v1.md"
RENDERED_PREPARATION = DATA / "opportunity-preparation-v2.md"

SELECTED_CLASS = DATA / "selected-quantity-class-v1.json"
QUALIFICATION = DATA / "globalping-counterpart-qualification-v4.json"
V2_DECISION = DATA / "v2-vantage-class-decision-v1.json"

CARRIED = (
    "target_actor",
    "observed_need_or_change",
    "candidate_intervention",
    "hypothesis_statement",
    "supported_dimensions",
    "unsupported_dimensions",
    "uncertainties",
)
STALE_MARKERS = ("MISSING_RELIABILITY", "no reviewed reliability applies", "NON_SCORABLE")
MIN_SCORING_ROWS_FOR_READY = 2
NON_OPPORTUNITY_COUNTERS = (
    "raw_records",
    "normalized_records",
    "signals",
    "claims",
    "claim_revisions",
    "evidence",
    "evidence_reliability_written",
    "reliability_assessments",
    "reliability_assessment_basis_rows",
    "independence_groups",
    "threshold_registrations",
    "claim_derivations",
    "proposition_evaluation_refusals",
    "embeddings",
    "sources",
    "source_reviews",
    "scores_table",
)


class ValidationError(Exception):
    pass


def _load(path: pathlib.Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _stale(sentence: str) -> bool:
    return any(marker in sentence for marker in STALE_MARKERS)


# ------------------------------------------------------------------------- checks


def _check_history_is_untouched(record: dict) -> None:
    v1 = record["historical_artifacts"]["preparation_v1"]
    if v1["path"] != f"docs/data/{PREPARATION_V1.name}":
        raise ValidationError("the historical preparation record is not v1")
    if hashlib.sha256(PREPARATION_V1.read_bytes()).hexdigest() != v1["sha256"]:
        raise ValidationError(
            "opportunity-preparation-v1.json no longer hashes to the recorded value"
        )
    historical = _load(PREPARATION_V1)
    if historical.get("mission") != "1.28" or "supersedes" in historical:
        raise ValidationError("the v1 preparation record was rewritten as though it were current")
    if historical["totals"]["evidence_rows_inspected"] == record["census"]["total_evidence"]:
        raise ValidationError("the historical packet carries the current census")
    applied = record["revision_2_applied"]
    if applied is None or not record["reconciled"]:
        raise ValidationError("no revision 2 is recorded")
    if not applied["revision_1_byte_identical_after"]:
        raise ValidationError("revision 1 differs after the reconciliation")
    before = record["revision_1"]
    after = applied["revision_1_after"]
    if before != after:
        raise ValidationError(
            f"revision 1 changed in {sorted(k for k in before if before[k] != after.get(k))}"
        )
    if not any(_stale(s) for s in before["epistemic_limitations"]):
        raise ValidationError(
            "revision 1's copy no longer carries the stale sentence; history was edited"
        )


def _check_the_hypothesis_is_not_strengthened(record: dict) -> None:
    one = record["revision_1"]
    two = record["revision_2_applied"]["revision_2_row"]
    for field in CARRIED:
        if one[field] != two[field]:
            raise ValidationError(
                f"revision 2 changed {field}; that is a resynthesis, not a reconciliation"
            )
    if two["model_version"] is not None or two["prompt_version"] is not None:
        raise ValidationError("revision 2 carries a model version; a reconciliation calls no model")
    if (
        two["opportunity_id"] != one["opportunity_id"]
        or two["opportunity_id"] != record["opportunity"]["id"]
    ):
        raise ValidationError("revision 2 belongs to a different Opportunity")
    if two["revision"] != one["revision"] + 1:
        raise ValidationError(
            f"revision numbers {one['revision']} -> {two['revision']} are not contiguous"
        )
    if record["revision_1_audit"]["hypothesis_statement_changed"]:
        raise ValidationError("the record admits the hypothesis changed")
    procedure = two["procedure_version"]
    if f"prior_revision={one['id']}" not in procedure:
        raise ValidationError("revision 2 does not name revision 1 as its prior")
    if f"reason={record['revision_reason']}" not in procedure or not procedure.startswith(
        record["procedure_version"]
    ):
        raise ValidationError("revision 2 carries no structured reason")
    if (
        record["counters"]["before_reconciliation"]["opportunities"]
        != record["counters"]["after"]["opportunities"]
    ):
        raise ValidationError("an Opportunity was created or removed")


def _check_the_evidence_set_is_not_widened(record: dict, preparation: dict) -> None:
    cited_before = {link["evidence_id"] for link in record["revision_1_links"]}
    written = record["revision_2_applied"]["links_written"]
    cited_after = {link["evidence_id"] for link in written}
    if cited_after != cited_before:
        raise ValidationError(
            f"revision 2 cites {sorted(cited_after - cited_before)} more and "
            f"{sorted(cited_before - cited_after)} fewer than revision 1"
        )
    rows = {r["evidence_id"]: r for r in preparation["rows"]}
    assessments = {a["assessment_id"]: a for a in record["revision_1_audit"]["why_stale"]}
    carried = {
        r["evidence_id"]: r for r in record["current_evidence"]["linked_by_revision_1_and_carried"]
    }
    if set(carried) != cited_before:
        raise ValidationError("the carried rows are not revision 1's links")
    for link in written:
        row = rows.get(link["evidence_id"])
        if row is None:
            raise ValidationError(f"{link['evidence_id'][:8]} is not in the current preparation")
        if link["eligibility_at_citation"] != row["eligibility"]:
            raise ValidationError(
                f"{link['evidence_id'][:8]}: eligibility at citation is not the current one"
            )
        resolution = row["reliability_resolution"]
        entry = carried[link["evidence_id"]]
        resolved = resolution["outcome"] == "RESOLVED"
        if entry["scorable"] != resolved or row["scorable"] != resolved:
            raise ValidationError(
                f"{link['evidence_id'][:8]}: scorable without a resolved binding, or the reverse"
            )
        if (row["eligibility"] == "ELIGIBLE_SCORING") != resolved:
            raise ValidationError(
                f"{link['evidence_id'][:8]}: ELIGIBLE_SCORING without the resolver"
            )
        if resolved:
            assessment = assessments.get(resolution["assessment_id"])
            if assessment is None:
                raise ValidationError(f"{link['evidence_id'][:8]}: bound to an unknown assessment")
            if assessment["source_id"] != row["source_id"]:
                raise ValidationError(
                    f"{link['evidence_id'][:8]}: a {row['source_id']} row carries a "
                    f"{assessment['source_id']} assessment"
                )
            if entry["resolved_reliability"] != assessment["reliability"]:
                raise ValidationError(
                    f"{link['evidence_id'][:8]}: reliability is not its assessment's"
                )
        elif entry["resolved_reliability"] is not None or entry["assessment_id"]:
            raise ValidationError(
                f"{link['evidence_id'][:8]}: a value on a row no assessment covers"
            )
    for row in record["current_evidence"]["in_current_packet_not_linked"]:
        if row["evidence_id"] in cited_after:
            raise ValidationError("a row is both linked and recorded as not linked")
        if row["classification"] != "REQUIRES_NEW_SEMANTIC_JUDGEMENT_BEFORE_INCLUSION":
            raise ValidationError(
                "an unlinked packet row was classified as linkable without a judgement"
            )


def _check_the_limitations(record: dict) -> None:
    one = record["revision_1"]["epistemic_limitations"]
    two = record["revision_2_applied"]["revision_2_row"]["epistemic_limitations"]
    stale = [s for s in one if _stale(s)]
    kept = [s for s in one if not _stale(s)]
    if not stale:
        raise ValidationError(
            "revision 1 carried nothing stale, so revision 2 has no reason to exist"
        )
    for sentence in stale:
        if sentence in two:
            raise ValidationError("the stale sentence survived into revision 2")
    for sentence in kept:
        if sentence not in two:
            raise ValidationError("a sentence Mission 1.77 did not touch was dropped")
    census = record["census"]
    new = [s for s in two if s not in kept]
    if len(new) != 1:
        raise ValidationError(
            f"revision 2 carries {len(new)} new sentences; the reconciliation adds exactly one"
        )
    sentence = new[0]
    if f"{census['scorable_linked_evidence']} of {census['linked_evidence']}" not in sentence:
        raise ValidationError("the new sentence's counts disagree with the links")
    if str(census["non_scorable_linked_evidence"]) not in sentence:
        raise ValidationError("the new sentence does not say how many rows remain non-scorable")
    for required in ("UNCALIBRATED", "no Score", "no ranking"):
        if required not in sentence:
            raise ValidationError(f"the new sentence does not say {required!r}")
    if "independence" not in " ".join(two).lower():
        raise ValidationError("revision 2 no longer states that independence is unestablished")
    audit = record["revision_1_audit"]["limitations"]
    for entry in audit:
        expected = (
            "STALE_DUE_TO_RELIABILITY_RESOLUTION_FIX"
            if _stale(entry["revision_1_sentence"])
            else "NOT_RELATED_TO_1_77"
        )
        if entry["classification"] != expected:
            raise ValidationError("a revision-1 sentence is misclassified")
    reasoning = record["revision_2_applied"]["revision_2_row"]["reasoning_summary"]
    if "MISSING_RELIABILITY" in reasoning:
        raise ValidationError("the reasoning summary still says MISSING_RELIABILITY")
    if "UNKNOWN independence" not in reasoning:
        raise ValidationError("the reasoning summary dropped the independence statement")


def _check_scoring_readiness_and_no_score(record: dict, preparation: dict) -> None:
    current = record["current_evidence"]
    packet = next(p for p in preparation["packets"] if p["packet_id"] == current["packet_id_now"])
    scoring_rows = packet["eligibility_counts"].get("ELIGIBLE_SCORING", 0)
    if packet["sufficiency"]["scoring_ready"] != (scoring_rows >= MIN_SCORING_ROWS_FOR_READY):
        raise ValidationError("the packet's scoring readiness disagrees with its contract")
    if current["scoring_ready_now_per_contract"] != packet["sufficiency"]["scoring_ready"]:
        raise ValidationError("the record's scoring readiness disagrees with the preparation")
    if "authorises nothing" not in current["scoring_ready_contract"]:
        raise ValidationError("scoring readiness is recorded as if it authorised a score")
    counters = record["counters"]
    for key in ("before_reconciliation", "after"):
        if counters[key]["scores_table"] != "ABSENT":
            raise ValidationError("a scores table exists")
        if counters[key]["independence_groups"] != 0:
            raise ValidationError("an independence group exists")
    if record["census"]["linked_independence_states"] != ["UNKNOWN"]:
        raise ValidationError("a linked row claims an independence state nobody established")
    census = record["census"]
    if (
        census["scorable_linked_evidence"] + census["non_scorable_linked_evidence"]
        != census["linked_evidence"]
    ):
        raise ValidationError("the linked census does not add up")
    if census["total_evidence"] != preparation["totals"]["evidence_rows_inspected"]:
        raise ValidationError("the census disagrees with the preparation")
    if census["scorable_evidence"] != preparation["totals"]["eligible_scoring"]:
        raise ValidationError("the scorable census disagrees with the preparation")
    if preparation.get("supersedes") != f"docs/data/{PREPARATION_V1.name}":
        raise ValidationError("the current preparation does not point back at v1")
    if "LINEAGE_LATE_RESOLUTION" not in preparation.get("reliability_resolution_path", ""):
        raise ValidationError("the current preparation did not resolve reliability late")
    stored = sum(
        1 for r in preparation["rows"] if r["reliability_resolution"]["outcome"] == "RESOLVED"
    )
    if stored != preparation["totals"]["eligible_scoring"]:
        raise ValidationError(
            "scoring eligibility disagrees with the resolver on the preparation rows"
        )
    for row in preparation["rows"]:
        if row["scorable"] != (row["reliability_resolution"]["outcome"] == "RESOLVED"):
            raise ValidationError(
                f"{row['evidence_id'][:8]}: scorability read from somewhere other than the resolver"
            )


def _check_nothing_else_moved(record: dict) -> None:
    before = record["counters"]["before_reconciliation"]
    after = record["counters"]["after"]
    moved = [k for k in NON_OPPORTUNITY_COUNTERS if before[k] != after[k]]
    if moved:
        raise ValidationError(f"non-Opportunity counters moved: {moved}")
    if after["opportunity_revisions"] != before["opportunity_revisions"] + 1:
        raise ValidationError("the reconciliation wrote other than exactly one revision")
    links = len(record["revision_2_applied"]["links_written"])
    if after["opportunity_evidence_links"] != before["opportunity_evidence_links"] + links:
        raise ValidationError("the link delta is not revision 2's links")
    newest = record["revision_2_applied"]["newest_revision_by_index"]
    if newest["id"] != record["revision_2_applied"]["revision_2_id"]:
        raise ValidationError("the newest revision by the canonical index is not revision 2")


def _check_the_parked_arc() -> None:
    states = _load(SELECTED_CLASS)["states_kept_apart"]
    if not states["CLASS_SELECTED"] or states["CONSTRUCT_SELECTED"] or states["RUN_AUTHORIZED"]:
        raise ValidationError("Q1 is no longer selected-without-construct-or-run")
    qualification = _load(QUALIFICATION)
    if {k: qualification["tally"][k] for k in ("PASS", "PARTIAL", "FAIL")} != {
        "PASS": 12,
        "PARTIAL": 0,
        "FAIL": 0,
    }:
        raise ValidationError("the Globalping tally moved")
    v2 = _load(V2_DECISION)
    if v2["corpus_frozen"] or v2["measurements_executed"] != 0:
        raise ValidationError("a corpus was frozen or a measurement executed")
    if (DATA / "selected-construct-v1.json").exists():
        raise ValidationError("a construct artifact exists")


def validate() -> tuple[dict, dict]:
    record = _load(RECONCILIATION)
    preparation = _load(PREPARATION_V2)
    try:
        _check_history_is_untouched(record)
        _check_the_hypothesis_is_not_strengthened(record)
        _check_the_evidence_set_is_not_widened(record, preparation)
        _check_the_limitations(record)
        _check_scoring_readiness_and_no_score(record, preparation)
        _check_nothing_else_moved(record)
        _check_the_parked_arc()
    except (KeyError, TypeError, IndexError, StopIteration) as error:
        raise ValidationError(f"the records do not carry {error!r}") from error
    return record, preparation


# ------------------------------------------------------------------------ renderers


def render_reconciliation(record: dict) -> str:
    applied = record["revision_2_applied"]
    two = applied["revision_2_row"]
    census = record["census"]
    lines = [
        "# Opportunity reliability reconciliation — revision 2, by supersession",
        "",
        f"Generated from `{RECONCILIATION.name}`. Do not edit by hand.",
        "",
        f"Opportunity `{record['opportunity']['id']}` (`{record['opportunity']['title']}`): revision "
        f"{record['revision_1']['revision']} of {record['revision_1']['created_at'][:10]} stays as written; "
        f"revision {two['revision']} of {two['created_at'][:10]} carries the same hypothesis over the same "
        f"{census['linked_evidence']} cited rows with the stale reliability sentences replaced. Reason "
        f"`{record['revision_reason']}`.",
        "",
        "## What Mission 1.77 made false, and what replaced it",
        "",
        "| revision 1 | classification |",
        "|---|---|",
    ]
    for entry in record["revision_1_audit"]["limitations"]:
        lines.append(f"| {entry['revision_1_sentence']} | `{entry['classification']}` |")
    lines += [
        "",
        "**Revision 2 limitations:**",
        "",
    ]
    lines += [f"{n}. {s}" for n, s in enumerate(two["epistemic_limitations"], 1)]
    lines += [
        "",
        "## The cited rows, through the current resolver",
        "",
        "| evidence | source | eligibility rev 1 → now | reliability | scorable | independence |",
        "|---|---|---|---|---|---|",
    ]
    for row in record["current_evidence"]["linked_by_revision_1_and_carried"]:
        lines.append(
            f"| `{row['evidence_id'][:8]}` | `{row['source_id']}` | {row['eligibility_at_revision_1']} → "
            f"{row['eligibility_now']} | {row['resolved_reliability'] if row['scorable'] else '—'} "
            f"| {row['scorable']} | {row['independence_state']} |"
        )
    lines += [
        "",
        f"In the current packet and not cited: {len(record['current_evidence']['in_current_packet_not_linked'])} rows, "
        "each requiring a semantic judgement this reconciliation does not make.",
        "",
        "## Census",
        "",
        "| | |",
        "|---|---|",
        f"| Evidence, total / scorable / non-scorable | {census['total_evidence']} / {census['scorable_evidence']} / {census['non_scorable_evidence']} |",
        f"| linked, total / scorable / non-scorable | {census['linked_evidence']} / {census['scorable_linked_evidence']} / {census['non_scorable_linked_evidence']} |",
        f"| linked dimensions | {', '.join(f'`{d}`' for d in census['linked_dimensions'])} |",
        f"| linked source families | {', '.join(census['linked_source_families'])} |",
        f"| linked reliability distribution | `{census['linked_reliability_distribution']}` |",
        f"| linked independence | {', '.join(census['linked_independence_states'])} |",
        f"| packet scoring-ready per contract | {record['current_evidence']['scoring_ready_now_per_contract']} — {record['current_evidence']['scoring_ready_contract']} |",
        "",
        "## Counters",
        "",
        "| counter | before | after |",
        "|---|---|---|",
    ]
    before = record["counters"]["before_reconciliation"]
    after = record["counters"]["after"]
    for key in after:
        lines.append(f"| {key} | {before[key]} | {after[key]} |")
    lines.append("")
    return "\n".join(lines)


def render_preparation(preparation: dict) -> str:
    totals = preparation["totals"]
    lines = [
        "# Opportunity preparation, current view (v2)",
        "",
        f"Generated from `{PREPARATION_V2.name}`. Do not edit by hand.",
        "",
        f"`{preparation['artifact_version']}`, supersedes `{preparation['supersedes']}` (kept as history). "
        f"Reliability: {preparation['reliability_resolution_path']}. Use profile `{preparation['use_profile_id']}`.",
        "",
        "| | |",
        "|---|---|",
    ]
    for key, value in totals.items():
        lines.append(f"| {key} | {value} |")
    lines += [
        "",
        "## Packets",
        "",
        "| packet | subject | rows | scoring | context | status | scoring-ready |",
        "|---|---|---|---|---|---|---|",
    ]
    for packet in preparation["packets"]:
        lines.append(
            f"| `{packet['packet_id'][:8]}` | {packet['subject']} | {packet['size']} "
            f"| {packet['eligibility_counts'].get('ELIGIBLE_SCORING', 0)} "
            f"| {packet['eligibility_counts'].get('ELIGIBLE_CONTEXT', 0)} | `{packet['sufficiency']['status']}` "
            f"| {packet['sufficiency']['scoring_ready']} |"
        )
    lines += ["", preparation["epistemic_note"], ""]
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()

    try:
        record, preparation = validate()
    except ValidationError as error:
        print(f"REFUSED  Opportunity reconciliation: {error}")
        return 1

    rendered = {
        RENDERED_RECONCILIATION: render_reconciliation(record),
        RENDERED_PREPARATION: render_preparation(preparation),
    }
    if args.check:
        for path, text in rendered.items():
            if not path.exists():
                print(f"DRIFT    {path.name} does not exist")
                return 1
            if path.read_text(encoding="utf-8") != text:
                print(f"DRIFT    {path.name} does not match its record")
                return 1
        print("ok       the Opportunity reconciliation matches its records")
        return 0

    for path, text in rendered.items():
        path.write_text(text, encoding="utf-8", newline="\n")
        print(f"wrote    {path.name} ({len(text.splitlines())} lines)")
    census = record["census"]
    print(
        f"revision {record['revision_1']['revision']} -> {record['revision_2_applied']['revision_2_number']}"
    )
    print(f"linked   {census['linked_evidence']}, scorable {census['scorable_linked_evidence']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
