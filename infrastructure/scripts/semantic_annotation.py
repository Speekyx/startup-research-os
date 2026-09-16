"""Mission 1.85.4 (N08-B). Human reference annotation workflow for the DEVELOPMENT split.

No command here writes a label. People write labels, in their own working copies, outside the repository.

    prepare  --annotator-id ID --origin HUMAN_OPERATOR|HUMAN_EXPERT|HUMAN_NON_EXPERT --out DIR
             Copy the blank development pack for one annotator (with their deterministic record order
             and an unfilled attestation) and render that split's surfaces into DIR. DIR must be
             outside the repository. Holdout is never prepared here.
    lint     PACK
             Run the full import validator on a working pack and print every problem. Writes nothing.
    import   PACK
             Validate a completed pack and write its committed form (states, offsets, digests; no
             quotes, no notes) to docs/data. Refuses on any problem.
    label    PACK
             Interactive form: shows each question from the local surfaces folder, asks the eight
             questions one by one, checks every pasted quote immediately and saves after each record.
             It never proposes an answer. Needs no database.
    analyse
             Read every committed development annotation file and write the composition and agreement
             report plus the adjudication queue. Needs at least two annotators. Chooses no threshold.

prepare, lint and import read the held records (DATABASE_URL). analyse reads committed files only.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import pathlib
import sys
from typing import Any

ROOT = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "packages/semantic-extraction-contract/python"))
sys.path.insert(0, str(ROOT / "infrastructure/scripts"))

from build_semantic_egress_eligibility import development_surfaces  # noqa: E402
from sros_semantic_extraction_contract.agreement import (  # noqa: E402
    analyse_composition,
    build_adjudication_queue,
)
from sros_semantic_extraction_contract.annotation import (  # noqa: E402
    ATTESTATION_FLAGS,
    ATTESTATION_ID,
    AnnotationOrigin,
    HoldoutAccessError,
    annotator_record_order,
    validate_annotation_pack,
)

DATA = ROOT / "docs" / "data"
CORPUS = DATA / "stack-overflow-semantic-evaluation-corpus-v1.json"
BLANK_DEVELOPMENT = DATA / "stack-overflow-semantic-label-pack-development-v1.json"
HOLDOUT_PACK_NAME = "stack-overflow-semantic-label-pack-holdout-v1.json"
CONTRACT = DATA / "first-person-semantic-extraction-contract-v1.json"
COMPOSITION = DATA / "stack-overflow-semantic-annotation-composition-development-v1.json"
QUEUE = DATA / "stack-overflow-semantic-adjudication-queue-development-v1.json"
ANNOTATION_GLOB = "stack-overflow-semantic-annotations-development-*-v1.json"


def dump(doc: Any) -> bytes:
    return (json.dumps(doc, indent=1, ensure_ascii=False) + "\n").encode("utf-8")


def split_ids() -> tuple[set[str], set[str]]:
    corpus = json.loads(CORPUS.read_text("utf-8"))
    dev = {r["normalized_record_id"] for r in corpus["records"] if r["split"] == "DEVELOPMENT"}
    hold = {r["normalized_record_id"] for r in corpus["records"] if r["split"] == "HOLDOUT"}
    return dev, hold


def refuse_holdout_path(path: pathlib.Path) -> None:
    if path.name == HOLDOUT_PACK_NAME or "holdout" in path.name.lower():
        raise HoldoutAccessError(f"{path.name}: development tooling does not open holdout material")


def prepare(annotator_id: str, origin: str, out: pathlib.Path) -> int:
    if out.resolve().is_relative_to(ROOT.resolve()):
        print(
            "REFUSED  a working copy holds licensed text and human labels; it lives outside the repository"
        )
        return 1
    if origin not in {o.value for o in AnnotationOrigin}:
        print(f"REFUSED  origin {origin!r} is not a human origin")
        return 1
    blank = json.loads(BLANK_DEVELOPMENT.read_text("utf-8"))
    dev, _ = split_ids()
    surfaces = development_surfaces()
    order = annotator_record_order("DEVELOPMENT", annotator_id, sorted(dev))
    by_id = {r["normalized_record_id"]: r for r in blank["records"]}
    working = dict(blank)
    working["$comment"] = (
        'WORKING COPY for one human annotator. Fill every UNLABELLED cell from the rendered surfaces in surfaces/. Do not use any model or assistant, do not look at another annotator\'s file, and keep this folder outside the repository. Evidence items are {"quote": exact text, "occurrence": n}; a subject is {"quote", "occurrence"} or null. Sign the attestation last.'
    )
    working["annotator_id"] = annotator_id
    working["reference_origin"] = origin
    working["blank_pack_sha256"] = hashlib.sha256(BLANK_DEVELOPMENT.read_bytes()).hexdigest()
    working["record_order"] = order
    working["records"] = [by_id[rid] for rid in order]
    working["attestation"] = {
        "attestation_id": ATTESTATION_ID,
        "annotator_id": annotator_id,
        "attested_at": None,
        **dict.fromkeys(ATTESTATION_FLAGS),
    }
    out.mkdir(parents=True, exist_ok=True)
    (out / "surfaces").mkdir(exist_ok=True)
    for position, rid in enumerate(order, start=1):
        (out / "surfaces" / f"{position:03d}-{rid}.txt").write_bytes(surfaces[rid].encode("utf-8"))
    target = out / f"pack-development-{annotator_id}.json"
    if target.exists():
        print(f"REFUSED  {target} exists; a working copy is never overwritten")
        return 1
    target.write_bytes(dump(working))
    print(f"prepared {len(order)} records for {annotator_id} in {out}")
    return 0


def _validate(path: pathlib.Path):
    refuse_holdout_path(path)
    pack = json.loads(path.read_text("utf-8"))
    dev, hold = split_ids()
    return validate_annotation_pack(
        pack,
        split="DEVELOPMENT",
        split_record_ids=dev,
        other_split_record_ids=hold,
        surfaces=development_surfaces(),
        blank_pack=json.loads(BLANK_DEVELOPMENT.read_text("utf-8")),
    )


def lint(path: pathlib.Path) -> int:
    report = _validate(path)
    for code, detail in report.refusals:
        print(f"{code:40} {detail}")
    print(
        "ok       the pack would import"
        if report.accepted
        else f"FAIL     {len(report.refusals)} problem(s)"
    )
    return 0 if report.accepted else 1


def import_pack(path: pathlib.Path) -> int:
    report = _validate(path)
    if not report.accepted or report.committed is None:
        for code, detail in report.refusals:
            print(f"{code:40} {detail}")
        print("REFUSED  nothing was imported")
        return 1
    annotator = report.committed["annotator_id"]
    target = DATA / f"stack-overflow-semantic-annotations-development-{annotator}-v1.json"
    if target.exists():
        print(f"REFUSED  {target.name} exists; an imported annotation is never replaced")
        return 1
    existing = [json.loads(p.read_text("utf-8")) for p in sorted(DATA.glob(ANNOTATION_GLOB))]
    if any(e["working_pack_sha256"] == report.committed["working_pack_sha256"] for e in existing):
        print("REFUSED  an identical working pack was already imported")
        return 1
    target.write_bytes(dump(report.committed))
    print(f"imported {target.name}")
    return 0


def label(path: pathlib.Path) -> int:
    from sros_semantic_extraction_contract.annotation_session import (
        SessionQuit,
        dumps,
        run_session,
        surface_matches,
    )

    refuse_holdout_path(path)
    if path.resolve().is_relative_to(ROOT.resolve()):
        print("REFUSED  a working pack lives outside the repository")
        return 1
    pack = json.loads(path.read_text("utf-8"))
    if pack.get("split") != "DEVELOPMENT":
        raise HoldoutAccessError("the interactive form opens DEVELOPMENT packs only")
    folder = path.parent / "surfaces"
    surfaces: dict[str, str] = {}
    for position, rid in enumerate(pack["record_order"], start=1):
        file = folder / f"{position:03d}-{rid}.txt"
        expected = next(
            r["surface_sha256"] for r in pack["records"] if r["normalized_record_id"] == rid
        )
        text = file.read_bytes().decode("utf-8") if file.exists() else ""
        if not surface_matches(text, expected):
            print(
                f"REFUSED  {file.name} is missing or does not match its digest; run prepare again in a new folder"
            )
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
        run_session(pack, surfaces, ask=input, say=print, save=save)
    except (SessionQuit, KeyboardInterrupt, EOFError):
        print(
            "\nArrêt. Tout ce qui a été confirmé est enregistré ; relance la même commande pour reprendre."
        )
        return 0
    print("\nTerminé. Vérifie maintenant avec la commande lint (elle a besoin de DATABASE_URL).")
    return 0


def analyse() -> int:
    files = [json.loads(p.read_text("utf-8")) for p in sorted(DATA.glob(ANNOTATION_GLOB))]
    if len(files) < 2:
        print(
            f"HUMAN_LABELS_PENDING  {len(files)} committed development annotation file(s); agreement needs at least two"
        )
        return 0
    COMPOSITION.write_bytes(
        dump(analyse_composition(files, json.loads(CONTRACT.read_text("utf-8"))))
    )
    QUEUE.write_bytes(dump({"split": "DEVELOPMENT", "queue": build_adjudication_queue(files)}))
    print(f"wrote {COMPOSITION.name} and {QUEUE.name}")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    p = sub.add_parser("prepare")
    p.add_argument("--annotator-id", required=True)
    p.add_argument("--origin", required=True)
    p.add_argument("--out", required=True)
    sub.add_parser("lint").add_argument("pack")
    sub.add_parser("import").add_argument("pack")
    sub.add_parser("label").add_argument("pack")
    sub.add_parser("analyse")
    args = parser.parse_args(argv)
    if args.command == "prepare":
        return prepare(args.annotator_id, args.origin, pathlib.Path(args.out))
    if args.command == "lint":
        return lint(pathlib.Path(args.pack))
    if args.command == "import":
        return import_pack(pathlib.Path(args.pack))
    if args.command == "label":
        return label(pathlib.Path(args.pack))
    return analyse()


if __name__ == "__main__":
    sys.exit(main())
