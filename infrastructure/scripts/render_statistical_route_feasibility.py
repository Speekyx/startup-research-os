"""Render the Mission 1.46 independence-route feasibility finding.

    docs/data/independent-statistical-route-feasibility-v1.json
            |
            v
    docs/data/independent-statistical-route-feasibility-v1.md

No database and no network, so `--check` runs in CI.

    uv run python infrastructure/scripts/render_statistical_route_feasibility.py
    uv run python infrastructure/scripts/render_statistical_route_feasibility.py --check
"""

from __future__ import annotations

import argparse
import json
import pathlib

ROOT = pathlib.Path(__file__).resolve().parents[2]
DOCS = ROOT / "docs" / "data"
SOURCE = DOCS / "independent-statistical-route-feasibility-v1.json"
OUT_MD = DOCS / "independent-statistical-route-feasibility-v1.md"

READINESS_LABELS = {True: "yes", False: "**no**"}


def validate(document: dict) -> list[str]:
    """The claims this artifact may not make, checked rather than trusted."""
    problems: list[str] = []
    if document.get("selected_route") is not None:
        problems.append("selected_route must be null: no route was found feasible")
    matrix = document["two_gate_matrix"]
    for pair, gates in matrix.items():
        if pair.startswith("$"):
            continue
        if gates["semantic_match"] == "YES" and gates["provenance_independence"] == "YES":
            problems.append(f"{pair}: YES + YES would be an independence-capable route")
    for pair in document["candidate_pairs"]:
        if pair["provenance_independence"] == "YES":
            problems.append(f"{pair['pair_id']}: provenance independence was not established")
    return problems


def render(document: dict) -> str:
    lines: list[str] = []
    lines.append("# Independent statistical evidence — route feasibility")
    lines.append("")
    lines.append(
        f"**`{document['artifact_version']}`**, Mission 1.46. Rendered from the authored "
        "record; edit the JSON, not this page."
    )
    lines.append("")
    lines.append(f"**Primary outcome: `{document['primary_outcome']}`.**")
    lines.append("")
    lines.append(document["selected_route_note"])
    lines.append("")
    lines.append("---")
    lines.append("")
    lines.append("## The rule that decided it")
    lines.append("")
    lines.append(document["the_rule_that_decided_it"])
    lines.append("")
    lines.append("## The two-gate matrix")
    lines.append("")
    lines.append("Only **YES + YES** qualifies (§7).")
    lines.append("")
    lines.append("| pair | same proposition? | independent provenance? | verdict |")
    lines.append("|---|---|---|---|")
    verdicts = {p["pair_id"]: p["verdict"] for p in document["candidate_pairs"]}
    for pair, gates in document["two_gate_matrix"].items():
        if pair.startswith("$"):
            continue
        lines.append(
            f"| `{pair}` | **{gates['semantic_match']}** | "
            f"**{gates['provenance_independence']}** | `{verdicts.get(pair, '')}` |"
        )
    lines.append("")
    lines.append("## Provenance chains")
    lines.append("")
    lines.append("*Who produced the measurement, not who published the endpoint (§5).*")
    lines.append("")
    for name, chain in document["provenance_chains"].items():
        if name.startswith("$"):
            continue
        lines.append(f"### `{name}`")
        lines.append("")
        lines.append(f"**Publisher:** {chain['publisher']} · **Dataset:** {chain['dataset']}")
        lines.append("")
        lines.append("Stated sources:")
        lines.append("")
        for stated in chain["stated_sources"]:
            lines.append(f"- {stated}")
        lines.append("")
        lines.append(f"**Underlying producer.** {chain['underlying_producer']}")
        lines.append("")
        lines.append(f"*Basis:* {chain['documentary_basis']}")
        lines.append("")
    lines.append("## The candidate pairs")
    lines.append("")
    for pair in document["candidate_pairs"]:
        lines.append(f"### {pair['pair_id']} — `{pair['verdict']}`")
        lines.append("")
        lines.append(f"- **A:** {pair['measurement_a']}")
        lines.append(f"- **B:** {pair['measurement_b']}")
        lines.append("")
        lines.append(
            f"**Same proposition? {pair['semantic_match']}.** {pair['semantic_match_note']}"
        )
        lines.append("")
        lines.append(
            f"**Independent provenance? {pair['provenance_independence']}.** "
            f"{pair['provenance_independence_note']}"
        )
        lines.append("")
        lines.append(
            f"**If forced, independence would be `{pair['independence_state_if_forced']}`.** "
            f"{pair['why_it_was_not_selected']}"
        )
        lines.append("")
    lines.append("## The structural finding")
    lines.append("")
    lines.append(document["the_structural_finding"])
    lines.append("")
    lines.append("## Governance and readiness")
    lines.append("")
    lines.append(document["governance"]["governance_note"])
    lines.append("")
    readiness = document["resource_readiness"]
    lines.append("| source | " + " | ".join(readiness["columns"]) + " |")
    lines.append("|---" * (len(readiness["columns"]) + 1) + "|")
    for source_id in ("world-bank", "eurostat", "fred"):
        cells = " | ".join(READINESS_LABELS[flag] for flag in readiness[source_id])
        lines.append(f"| `{source_id}` | {cells} |")
    lines.append("")
    for key in ("geography", "unit", "temporal", "revision"):
        lines.append(f"## {key.capitalize()}")
        lines.append("")
        lines.append(document[key]["finding"])
        lines.append("")
    lines.append("## Reliability")
    lines.append("")
    for source_id in ("world-bank", "eurostat", "fred"):
        lines.append(f"- **`{source_id}`** — {document['reliability'][source_id]}")
    lines.append("")
    lines.append(document["reliability"]["note"])
    lines.append("")
    lines.append("## Claim architecture")
    lines.append("")
    architecture = document["claim_architecture"]
    lines.append(architecture["current_shape"])
    lines.append("")
    lines.append(f"**{architecture['consequence']}**")
    lines.append("")
    for route in architecture["the_two_available_routes"]:
        lines.append(f"- {route}")
    lines.append("")
    lines.append(architecture["which_would_be_required"])
    lines.append("")
    lines.append("## Can the model represent two groups?")
    lines.append("")
    lines.append(document["architecture_check"]["finding"])
    lines.append("")
    lines.append(f"**What is missing:** {document['architecture_check']['what_is_missing']}")
    lines.append("")
    lines.append("## A qualified alternative")
    lines.append("")
    alternative = document["qualified_alternative"]
    lines.append(f"**{alternative['finding']}**")
    lines.append("")
    lines.append(alternative["direction_rather_than_a_candidate"])
    lines.append("")
    lines.append(alternative["not_recommended_as_a_next_mission"])
    lines.append("")
    lines.append("## Network activity")
    lines.append("")
    activity = document["network_activity"]
    lines.append(f"- **`RESEARCH_DATA_REQUESTS` = {activity['RESEARCH_DATA_REQUESTS']}**")
    lines.append(
        f"- `STATISTICAL_DOCUMENTATION_REQUESTS` = {activity['STATISTICAL_DOCUMENTATION_REQUESTS']}"
        f", of which `METADATA_ONLY` = {activity['METADATA_ONLY']}"
    )
    lines.append(f"- `GOVERNANCE_DOCUMENT_REQUESTS` = {activity['GOVERNANCE_DOCUMENT_REQUESTS']}")
    lines.append("")
    for entry in activity["detail"]:
        lines.append(f"  - {entry}")
    lines.append("")
    lines.append(activity["note"])
    lines.append("")
    lines.append("## What this is not")
    lines.append("")
    for item in document["what_this_is_not"]:
        lines.append(f"- {item}")
    lines.append("")
    lines.append("## Next")
    lines.append("")
    nxt = document["next_mission"]
    lines.append(f"**{nxt['recommendation']}**")
    lines.append("")
    lines.append(f"- *Why not acquisition:* {nxt['why_not_acquisition']}")
    lines.append(f"- *Why not calibration:* {nxt['why_not_calibration']}")
    lines.append("")
    lines.append(nxt["the_open_question_worth_a_mission"])
    lines.append("")
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", help="compare and write nothing")
    args = parser.parse_args()

    document = json.loads(SOURCE.read_text(encoding="utf-8"))

    problems = validate(document)
    if problems:
        print("REFUSED: the feasibility record claims something it may not")
        for problem in problems:
            print(f"  - {problem}")
        return 1

    markdown = render(document)

    if args.check:
        if not OUT_MD.exists():
            print(f"REFUSED: {OUT_MD.name} does not exist; run without --check first")
            return 1
        if OUT_MD.read_text(encoding="utf-8") != markdown:
            print(f"DRIFT    {OUT_MD.name} does not match the record")
            return 1
        print(f"ok       {OUT_MD.name} matches the feasibility record")
        return 0

    OUT_MD.write_text(markdown, encoding="utf-8")
    print(f"outcome        : {document['primary_outcome']}")
    print(f"selected route : {document['selected_route'] or 'none'}")
    print(f"pairs reviewed : {len(document['candidate_pairs'])}")
    print(f"\nwrote {OUT_MD.name}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
