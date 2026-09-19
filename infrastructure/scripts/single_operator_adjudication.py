"""Mission 1.85.15 (N08-B-PILOT). The single-operator adjudication protocol, step by step.

There is no second annotator, so this builds a reference adjudicated by the only human available and says so.
Protocol: `sros_semantic_extraction_contract.single_operator_adjudication`.

    prepare-reread       --out DIR    the reread pack (46 EGRESS_APPROVED records, the two extractable labels,
                                      every cell UNLABELLED, a fresh order) and the rendered surfaces. DATABASE_URL.
    reread               PACK         the original terminal form, limited to the two labels. No database. Protocol
                                      1.1.0 (Mission 1.85.16) has no mandatory delay; a pack prepared under 1.0.0
                                      is refused and must be prepared again.
    import-reread        PACK         validate and commit the reread (states, offsets, digests). DATABASE_URL.
    prepare-adjudication --out DIR    after the reread: the cells whose readings disagree or are UNCERTAIN, with
                                      every reading, the post-model notes and the model's quotes. DATABASE_URL.
    adjudicate           DIR          terminal session: one final state and a reason per cell. No database.
    import-adjudication  DIR          validate every decision and commit the adjudicated reference. DATABASE_URL.
    check                             verify whatever has been committed so far. No database.

Material with question text lives outside the repository. No path here calls a model or a provider, and the
original blind annotation is read, never written.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import pathlib
import sys
from datetime import datetime
from typing import Any

ROOT = pathlib.Path(__file__).resolve().parents[2]
for _path in ("packages/semantic-extraction-contract/python", "packages/contracts/python"):
    sys.path.insert(0, str(ROOT / _path))
sys.path.insert(0, str(ROOT / "infrastructure/scripts"))

from sros_semantic_extraction_contract.annotation import annotator_record_order  # noqa: E402
from sros_semantic_extraction_contract.labels import LABELS  # noqa: E402
from sros_semantic_extraction_contract.single_operator_adjudication import (  # noqa: E402
    MINIMUM_DELAY_POLICY,
    PROTOCOL_ID,
    READING,
    REREAD_ATTESTATION,
    REREAD_LABELS,
    AdjudicationRefusedError,
    build_reference,
    cells_to_adjudicate,
    implied_state,
    intra_rater_agreement,
    make_adjudication,
    validate_reread_pack,
)

DATA = ROOT / "docs" / "data"
ORIGINAL = DATA / "stack-overflow-semantic-annotations-development-operator-a-v1.json"
ORIGINAL_SHA256 = "449ff10f8a60217bbf4b7887254cf81b492fdba962b39283f39d2acdf1a9fa3c"
ELIGIBILITY = DATA / "stack-overflow-semantic-egress-eligibility-development-v1.json"
CORPUS = DATA / "stack-overflow-semantic-evaluation-corpus-v1.json"
REVIEWS = (
    DATA / "semantic-extraction-post-model-review-development-v1.json",
    DATA / "semantic-extraction-balanced-post-model-review-development-v1.json",
)
RUN_SUMMARY = DATA / "semantic-extraction-pilot-run-development-v2.json"
REREAD = DATA / "stack-overflow-semantic-reread-development-operator-a-v1.json"
REFERENCE = DATA / "stack-overflow-semantic-single-human-adjudicated-reference-development-v1.json"
REFERENCE_PAGE = (
    DATA / "stack-overflow-semantic-single-human-adjudicated-reference-development-v1.md"
)
OPERATOR = "operator-a"
REREAD_ORDER_ID = "operator-a-delayed-reread"
PACK_NAME = "reread-pack-operator-a.json"
MATERIAL_NAME = "adjudication-material.json"
WORKING_NAME = "adjudication-working-operator-a.json"


def sha(path: pathlib.Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load(path: pathlib.Path) -> Any:
    return json.loads(path.read_text("utf-8"))


def dump(doc: Any) -> bytes:
    return (json.dumps(doc, indent=1, ensure_ascii=False) + "\n").encode("utf-8")


def now() -> str:
    return datetime.now().astimezone().isoformat(timespec="seconds")


def outside_repository(path: pathlib.Path) -> bool:
    return not path.resolve().is_relative_to(ROOT.resolve())


def original() -> dict[str, Any]:
    if sha(ORIGINAL) != ORIGINAL_SHA256:
        raise SystemExit(
            "REFUSED  the original blind annotation is not the one the pilots were read against"
        )
    return load(ORIGINAL)


def scope_ids() -> set[str]:
    corpus = load(CORPUS)
    development = {
        r["normalized_record_id"] for r in corpus["records"] if r["split"] == "DEVELOPMENT"
    }
    approved = set(load(ELIGIBILITY)["approved_record_ids"])
    if not approved <= development:
        raise SystemExit("REFUSED  the scope must be a subset of DEVELOPMENT")
    return approved


def last_exposure() -> str:
    """The latest moment the operator saw model output on these records: the last post-model decision."""
    return max(d["decided_at"] for path in REVIEWS for d in load(path)["decisions"])


def post_model_states() -> tuple[dict[str, str], dict[str, dict[str, Any]]]:
    """The state each REPORTED_FAILED_ATTEMPT post-model decision implies, and the decision itself. The two
    reviews cover disjoint records; if one ever covered a record twice, the later decision would govern."""
    decisions: dict[str, dict[str, Any]] = {}
    for path in REVIEWS:
        for d in load(path)["decisions"]:
            decisions[d["normalized_record_id"]] = d
    return {rid: implied_state(d["decision"]) for rid, d in decisions.items()}, decisions


def surfaces_for(ids: set[str]) -> dict[str, str]:
    from build_semantic_egress_eligibility import development_surfaces

    surfaces = development_surfaces()
    return {rid: surfaces[rid] for rid in ids}


# -- step 1: the delayed reread ---------------------------------------------------------------------------


def prepare_reread(out: pathlib.Path) -> int:
    if not outside_repository(out):
        print("REFUSED  the reread folder holds question text; it lives outside the repository")
        return 1
    if REREAD.exists():
        print("REFUSED  the reread is already committed; it is done once")
        return 1
    target = out / PACK_NAME
    if target.exists():
        print(
            f"REFUSED  {target} exists; a reread pack is never overwritten (run reread to resume)"
        )
        return 1
    ids = scope_ids()
    surfaces = surfaces_for(ids)
    order = annotator_record_order("DEVELOPMENT", REREAD_ORDER_ID, sorted(ids))
    digests = {r["normalized_record_id"]: r["surface_sha256"] for r in load(CORPUS)["records"]}
    pack = {
        "$comment": "REREAD by the operator. Answer from the text only. Your earlier labels, the reviews and the model's answers are not shown here; do not look them up while you read.",
        "protocol": PROTOCOL_ID,
        "reading": READING,
        "split": "DEVELOPMENT",
        "operator_id": OPERATOR,
        "record_scope": "DEVELOPMENT_EGRESS_APPROVED",
        "minimum_delay_policy": MINIMUM_DELAY_POLICY[PROTOCOL_ID],
        "record_order": order,
        "annotation_started_at": None,
        "annotation_completed_at": None,
        "attestation": {"attested_at": None, **dict.fromkeys(REREAD_ATTESTATION)},
        "records": [
            {
                "normalized_record_id": rid,
                "surface_sha256": digests[rid],
                "labels": {
                    label: {"state": "UNLABELLED", "evidence": [], "subject": None, "note": None}
                    for label in REREAD_LABELS
                },
            }
            for rid in order
        ],
    }
    out.mkdir(parents=True, exist_ok=True)
    (out / "surfaces").mkdir(exist_ok=True)
    for position, rid in enumerate(order, start=1):
        (out / "surfaces" / f"{position:03d}-{rid}.txt").write_bytes(surfaces[rid].encode("utf-8"))
    target.write_bytes(dump(pack))
    print(
        f"prepared the reread of {len(order)} records in {out}; it may start now (no mandatory delay)"
    )
    return 0


def superseded(pack: dict[str, Any]) -> str | None:
    """Why a pack cannot be used under the current protocol, or None."""
    if pack.get("protocol") == PROTOCOL_ID:
        return None
    return (
        f"this pack was prepared under {pack.get('protocol')}; {PROTOCOL_ID} supersedes it for future rereads, "
        "so prepare a new pack into a new folder (nothing is patched in place)"
    )


def reread(path: pathlib.Path) -> int:
    from sros_semantic_extraction_contract.annotation_session import (
        SessionQuit,
        dumps,
        run_session,
        surface_matches,
    )

    if not outside_repository(path):
        print("REFUSED  a reread pack lives outside the repository")
        return 1
    pack = load(path)
    reason = superseded(pack)
    if reason:
        print(f"REFUSED  {reason}")
        return 1
    surfaces: dict[str, str] = {}
    for position, rid in enumerate(pack["record_order"], start=1):
        file = path.parent / "surfaces" / f"{position:03d}-{rid}.txt"
        expected = next(
            r["surface_sha256"] for r in pack["records"] if r["normalized_record_id"] == rid
        )
        text = file.read_bytes().decode("utf-8") if file.exists() else ""
        if not surface_matches(text, expected):
            print(f"REFUSED  {file.name} is missing or does not match its digest")
            return 1
        surfaces[rid] = text
    for stream in (sys.stdout, sys.stderr):
        reconfigure = getattr(stream, "reconfigure", None)
        if reconfigure is not None:
            reconfigure(encoding="utf-8")

    def save(current: dict[str, Any]) -> None:
        temporary = path.with_suffix(".json.tmp")
        temporary.write_bytes(dumps(current).encode("utf-8"))
        temporary.replace(path)

    try:
        run_session(
            pack,
            surfaces,
            ask=input,
            say=print,
            save=save,
            label_ids=REREAD_LABELS,
            attestation_wording=REREAD_ATTESTATION,
        )
    except (SessionQuit, KeyboardInterrupt, EOFError):
        print(
            "\nArrêt. Tout ce qui a été confirmé est enregistré ; relance la même commande pour reprendre."
        )
        return 0
    print("\nTerminé. Importe maintenant la relecture (import-reread, avec DATABASE_URL).")
    return 0


def import_reread(path: pathlib.Path) -> int:
    if REREAD.exists():
        print(f"REFUSED  {REREAD.name} exists; the reread is committed once")
        return 1
    pack = load(path)
    reason = superseded(pack)
    if reason:
        print(f"REFUSED  {reason}")
        return 1
    ids = scope_ids()
    refusals, committed = validate_reread_pack(
        pack, scope_record_ids=ids, surfaces=surfaces_for(ids)
    )
    if committed is None:
        for code, detail in refusals:
            print(f"{code:44} {detail}")
        print("REFUSED  nothing was imported")
        return 1
    committed["inputs"] = {"original_sha256": sha(ORIGINAL), "last_exposure": last_exposure()}
    REREAD.write_bytes(dump(committed))
    print(f"imported {REREAD.name}")
    return 0


# -- step 2: adjudication ---------------------------------------------------------------------------------


def queue() -> list[dict[str, Any]]:
    states, _ = post_model_states()
    return cells_to_adjudicate(original(), load(REREAD), states)


def prepare_adjudication(out: pathlib.Path) -> int:
    if not outside_repository(out):
        print("REFUSED  adjudication material holds question text; it lives outside the repository")
        return 1
    if not REREAD.exists():
        print("REFUSED  the reread must be committed before anything is adjudicated")
        return 1
    if (out / WORKING_NAME).exists():
        print("REFUSED  an adjudication working file exists; run adjudicate to resume")
        return 1
    items = queue()
    ids = {i["normalized_record_id"] for i in items}
    surfaces = surfaces_for(ids)
    first = {r["normalized_record_id"]: r["labels"] for r in original()["records"]}
    second = {r["normalized_record_id"]: r["labels"] for r in load(REREAD)["records"]}
    _, decisions = post_model_states()
    run = {r["normalized_record_id"]: r for r in load(RUN_SUMMARY)["records"]}

    def quotes(surface: str, cell: dict[str, Any]) -> list[dict[str, Any]]:
        return [
            {"start": s["start"], "end": s["end"], "quote": surface[s["start"] : s["end"]]}
            for s in cell.get("spans", [])
            if hashlib.sha256(surface[s["start"] : s["end"]].encode("utf-8")).hexdigest()
            == s["quote_sha256"]
        ]

    material = []
    for item in items:
        rid, lid = item["normalized_record_id"], item["label_id"]
        surface = surfaces[rid]
        extraction = (run.get(rid) or {}).get("extraction") or {}
        review = decisions.get(rid) if lid == "REPORTED_FAILED_ATTEMPT" else None
        material.append(
            {
                **item,
                "surface": surface,
                "original_spans": quotes(surface, first[rid][lid]),
                "reread_spans": quotes(surface, second[rid][lid]),
                "post_model_decision": review["decision"] if review else None,
                "post_model_note": review.get("operator_note") if review else None,
                "model_prompt_1_1_quotes": [
                    surface[f["evidence_start"] : f["evidence_end"]]
                    for f in extraction.get("findings", [])
                    if f["finding_type"] == lid
                ],
            }
        )
    out.mkdir(parents=True, exist_ok=True)
    (out / MATERIAL_NAME).write_bytes(
        dump({"$comment": "LOCAL ADJUDICATION MATERIAL. Never commit.", "items": material})
    )
    (out / WORKING_NAME).write_bytes(
        dump({"protocol": PROTOCOL_ID, "operator_id": OPERATOR, "decisions": []})
    )
    print(f"prepared {len(items)} cells to adjudicate in {out}")
    return 0


def adjudicate(folder: pathlib.Path, ask: Any = input, say: Any = print, clock: Any = now) -> int:
    from sros_semantic_extraction_contract.annotation_session import _quote

    material = load(folder / MATERIAL_NAME)["items"]
    working_path = folder / WORKING_NAME
    working = load(working_path)
    done = {(d["normalized_record_id"], d["label_id"]) for d in working["decisions"]}

    def read(prompt: str, allowed: set[str]) -> str:
        while True:
            answer = ask(prompt).strip().lower()
            if answer in allowed:
                return answer

    for position, item in enumerate(material, start=1):
        key = (item["normalized_record_id"], item["label_id"])
        if key in done:
            continue
        say("=" * 78)
        say(
            f"CELLULE {position}/{len(material)}  {item['label_id']}  {item['normalized_record_id']}"
        )
        say("=" * 78)
        say(item["surface"])
        say("=" * 78)
        for name, state in item["readings"].items():
            say(f"  {name:20} {state}")
        for name in ("original_spans", "reread_spans"):
            for span in item[name]:
                say(f"  [{name}] {span['quote']}")
        if item["post_model_decision"]:
            say(f"  Revue post-modèle : {item['post_model_decision']}")
            if item["post_model_note"]:
                say(f"    note : {item['post_model_note']}")
        for quote in item["model_prompt_1_1_quotes"]:
            say(f"  [modèle, prompt 1.1.0] {quote}")
        answer = read(
            "  État final : o = PRESENT, n = ABSENT, ? = UNCERTAIN, q = quitter : ",
            {"o", "n", "?", "q"},
        )
        if answer == "q":
            say("Arrêt. Les décisions confirmées sont enregistrées.")
            return 0
        state = {"o": "PRESENT", "n": "ABSENT", "?": "UNCERTAIN"}[answer]
        note = ""
        while not note.strip():
            note = ask("  Raison, avec tes propres mots (obligatoire) : ")
        spans: list[dict[str, Any]] = []
        subject = None
        surface = item["surface"]
        if state == "PRESENT":
            offered = item["original_spans"] + item["reread_spans"]
            for index, span in enumerate(offered, start=1):
                say(f"  {index}. {span['quote']}")
            choice = read(
                "  Preuve : numéro d'une phrase ci-dessus, ou c pour en coller une autre : ",
                {str(i) for i in range(1, len(offered) + 1)} | {"c"},
            )
            if choice == "c":
                forbid_code = not next(
                    lbl for lbl in LABELS if lbl.label_id == item["label_id"]
                ).evidence_may_be_in_code
                pasted = _quote(ask, say, surface, subject=False, forbid_code=forbid_code)
                start = _nth(surface, pasted["quote"], pasted["occurrence"])
                spans = [_committed_span(surface, start, start + len(pasted["quote"]))]
            else:
                chosen = offered[int(choice) - 1]
                spans = [_committed_span(surface, chosen["start"], chosen["end"])]
            if item["label_id"] == "NEGATIVE_EVALUATION_OF_NAMED_SOLUTION":
                named = _quote(ask, say, surface, subject=True, forbid_code=True)
                start = _nth(surface, named["quote"], named["occurrence"])
                subject = _committed_span(surface, start, start + len(named["quote"]))
        try:
            decision = make_adjudication(
                item,
                final_state=state,
                note=note,
                spans=spans,
                subject=subject,
                decided_at=clock(),
                operator_id=OPERATOR,
            )
        except AdjudicationRefusedError as exc:
            say(f"  Refusé : {exc}. Recommence cette cellule.")
            return adjudicate(folder, ask, say, clock)
        working["decisions"].append(decision)
        temporary = working_path.with_suffix(".json.tmp")
        temporary.write_bytes(dump(working))
        temporary.replace(working_path)
        say("  Enregistré.")
    say(
        "Toutes les cellules sont décidées. Importe maintenant l'adjudication (import-adjudication)."
    )
    return 0


def _nth(surface: str, quote: str, occurrence: int) -> int:
    start = -1
    for _ in range(occurrence):
        start = surface.index(quote, start + 1)
    return start


def _committed_span(surface: str, start: int, end: int) -> dict[str, Any]:
    return {
        "start": start,
        "end": end,
        "quote_sha256": hashlib.sha256(surface[start:end].encode("utf-8")).hexdigest(),
        "quote_length": end - start,
    }


def render(decisions: list[dict[str, Any]]) -> tuple[dict[str, Any], bytes]:
    states, _ = post_model_states()
    first, second = original(), load(REREAD)
    reference = build_reference(first, second, states, decisions)
    doc = {
        "$comment": "SINGLE-HUMAN ADJUDICATED REFERENCE (Mission 1.85.15). Built by the only human available from their original blind labels, their delayed reread and, where they disagreed, their adjudication after seeing every reading and the model's answer. NOT consensus, NOT inter-human, NOT blind, NOT certification; the original blind annotation is unchanged and remains the reference every preregistered reading used. States, offsets and digests only.",
        "reference_id": "stack-overflow-semantic-single-human-adjudicated-reference-development",
        "version": "1.0.0",
        "inputs": {
            "original_sha256": sha(ORIGINAL),
            "reread_sha256": sha(REREAD),
            "reviews_sha256": [sha(p) for p in REVIEWS],
        },
        **reference,
        "intra_rater_agreement": intra_rater_agreement(first, second),
        "adjudications": sorted(
            decisions, key=lambda d: (d["label_id"], d["normalized_record_id"])
        ),
    }
    lines = [
        "# Single-human adjudicated reference, DEVELOPMENT (v1)",
        "",
        "> Generated by `infrastructure/scripts/single_operator_adjudication.py`. Do not edit by hand.",
        "",
        f"`{reference['reference_strength']}`: one operator, original blind labels + a delayed reread + adjudication of {reference['cells_adjudicated']} disputed cells. Not consensus, not inter-human, not blind, not certification. The original blind annotation is unchanged.",
        "",
    ]
    for label_id, counts in reference["state_counts"].items():
        agreement = doc["intra_rater_agreement"]["labels"][label_id]
        lines += [
            f"## {label_id}",
            "",
            f"Adjudicated reference {json.dumps(counts)}. Intra-rater (original vs reread, one person): raw {agreement['raw_agreement_three_state']}, kappa {agreement['cohen_kappa_three_state']}.",
            "",
            "| Record | Readings | Final | Basis |",
            "|---|---|---|---|",
        ]
        for d in doc["adjudications"]:
            if d["label_id"] == label_id:
                readings = ", ".join(f"{k} {v}" for k, v in d["readings"].items())
                lines.append(
                    f"| `{d['normalized_record_id'][:8]}` | {readings} | {d['final_state']} | adjudicated |"
                )
        lines.append("")
    return doc, "\n".join(lines).encode("utf-8")


def import_adjudication(folder: pathlib.Path) -> int:
    if REFERENCE.exists():
        print(f"REFUSED  {REFERENCE.name} exists; the adjudicated reference is committed once")
        return 1
    decisions = load(folder / WORKING_NAME)["decisions"]
    items = {(i["normalized_record_id"], i["label_id"]): i for i in queue()}
    surfaces = surfaces_for({rid for rid, _ in items})
    problems = []
    for d in decisions:
        key = (d["normalized_record_id"], d["label_id"])
        if key not in items:
            problems.append(f"NOT_A_CELL_TO_ADJUDICATE {key}")
            continue
        surface = surfaces[key[0]]
        for span in d["spans"] + ([d["subject"]] if d["subject"] else []):
            text = surface[span["start"] : span["end"]]
            if hashlib.sha256(text.encode("utf-8")).hexdigest() != span["quote_sha256"]:
                problems.append(f"SPAN_NOT_IN_SURFACE {key}")
    if problems:
        print("\n".join(problems) + "\nREFUSED  nothing was imported")
        return 1
    try:
        doc, page = render(decisions)
    except AdjudicationRefusedError as exc:
        print(f"REFUSED  {exc}")
        return 1
    REFERENCE.write_bytes(dump(doc))
    REFERENCE_PAGE.write_bytes(page)
    print(f"imported {REFERENCE.name}: {doc['cells_adjudicated']} cells adjudicated")
    return 0


def check() -> int:
    if not REREAD.exists():
        if REFERENCE.exists():
            print("FAIL     an adjudicated reference exists without a committed reread")
            return 1
        print("ok       WAITING_FOR_SINGLE_OPERATOR_DELAYED_REREAD: nothing committed yet")
        return 0
    reread_doc = load(REREAD)
    if (
        reread_doc.get("is_a_second_annotator") is not False
        or reread_doc.get("blind_to_model_outputs") is not False
    ):
        print("FAIL     the reread claims to be a second annotator or blind to model output")
        return 1
    if not REFERENCE.exists():
        print(
            f"ok       WAITING_FOR_SINGLE_OPERATOR_ADJUDICATION: reread committed, {len(queue())} cells to adjudicate"
        )
        return 0
    committed = load(REFERENCE)
    try:
        doc, page = render(committed["adjudications"])
    except AdjudicationRefusedError as exc:
        print(f"FAIL     {exc}")
        return 1
    if dump(doc) != REFERENCE.read_bytes() or page != REFERENCE_PAGE.read_bytes():
        print(f"FAIL     {REFERENCE.name} is stale or not reproducible")
        return 1
    print(f"ok       {REFERENCE.name} matches ({doc['cells_adjudicated']} cells adjudicated)")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("prepare-reread").add_argument("--out", required=True)
    sub.add_parser("reread").add_argument("pack")
    sub.add_parser("import-reread").add_argument("pack")
    sub.add_parser("prepare-adjudication").add_argument("--out", required=True)
    sub.add_parser("adjudicate").add_argument("folder")
    sub.add_parser("import-adjudication").add_argument("folder")
    sub.add_parser("check")
    args = parser.parse_args(argv)
    for stream in (sys.stdout, sys.stderr):
        reconfigure = getattr(stream, "reconfigure", None)
        if reconfigure is not None:
            reconfigure(encoding="utf-8")
    commands = {
        "prepare-reread": lambda: prepare_reread(pathlib.Path(args.out)),
        "reread": lambda: reread(pathlib.Path(args.pack)),
        "import-reread": lambda: import_reread(pathlib.Path(args.pack)),
        "prepare-adjudication": lambda: prepare_adjudication(pathlib.Path(args.out)),
        "adjudicate": lambda: adjudicate(pathlib.Path(args.folder)),
        "import-adjudication": lambda: import_adjudication(pathlib.Path(args.folder)),
        "check": check,
    }
    return commands[args.command]()


if __name__ == "__main__":
    sys.exit(main())
