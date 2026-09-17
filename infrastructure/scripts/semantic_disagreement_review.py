"""Mission 1.85.10 (N08-B-PILOT). Post-model operator review of the REPORTED_FAILED_ATTEMPT disagreements.

The review set is derived, not typed: every record where the Mission 1.85.9 pilot's accepted extraction marked
REPORTED_FAILED_ATTEMPT PRESENT and the blind single-human reference marked it ABSENT. This tool makes NO
choice. It shows the operator each record, the untouched blind reference, the model's quoted evidence rebuilt
from the frozen surface and the committed offsets, and the frozen label definition, and records only what
the operator clicks.

    prepare  --out DIR --operator-id ID
             Write the review material (exact surfaces, rebuilt quotes and context) and an empty working
             file into DIR, outside the repository. Reads the held surfaces (DATABASE_URL).
    serve    DIR [--port N]
             A local page on 127.0.0.1 only. No database, no network beyond loopback, no external asset.
             Every click is saved at once; serving again resumes.
    lint     WORKING
             Validate the working file against freshly computed inputs. Writes nothing (DATABASE_URL).
    import   WORKING
             Refuse unless valid and every record carries a choice, then write the committed review
             (bounded metadata only) with counts, recommendations and a labelled post-hoc diagnostic.
    check    Verify the committed review, if any, against the committed inputs. No database.

No path here calls a model or a provider. The blind annotation file is read, never written.
"""

from __future__ import annotations

import argparse
import hashlib
import html
import http.server
import json
import pathlib
import secrets
import sys
from datetime import datetime
from typing import Any

ROOT = pathlib.Path(__file__).resolve().parents[2]
for _path in ("packages/semantic-extraction-contract/python", "packages/contracts/python"):
    sys.path.insert(0, str(ROOT / _path))
sys.path.insert(0, str(ROOT / "infrastructure/scripts"))

from sros_semantic_extraction_contract import surface_sha256  # noqa: E402
from sros_semantic_extraction_contract.labels import (  # noqa: E402
    LABEL_SET_ID,
    LABEL_SET_VERSION,
    LABELS,
)
from sros_semantic_extraction_contract.post_model_review import (  # noqa: E402
    AMBIGUOUS,
    CHOICES,
    LABEL,
    NOTE_REQUIRED,
    OVERREAD,
    PROVENANCE,
    REVIEW_ID,
    REVISION,
    UNRESOLVED,
    ReviewRefusedError,
    analyse,
    blank_working_file,
    canonical_sha256,
    findings_digest,
    make_decision,
    review_status,
    validate_working,
)

DATA = ROOT / "docs" / "data"
PACKET = DATA / "semantic-extraction-evaluation-packet-development-v1.json"
APPROVAL = DATA / "semantic-extraction-evaluation-approval-development-v1.json"
SUMMARY = DATA / "semantic-extraction-pilot-run-development-v1.json"
EVALUATION = DATA / "semantic-extraction-pilot-evaluation-development-v1.json"
ANNOTATION = DATA / "stack-overflow-semantic-annotations-development-operator-a-v1.json"
CONTRACT = DATA / "first-person-semantic-extraction-contract-v1.json"
# The prompt in effect during the Mission 1.85.9 run, frozen when 1.1.0 replaced it (Mission 1.85.11).
PROMPT_SOURCE = (
    ROOT / "packages/semantic-extraction/python/sros_semantic_extraction/prompt_v1_0_0.py"
)
REVIEW = DATA / "semantic-extraction-post-model-review-development-v1.json"
REVIEW_PAGE = DATA / "semantic-extraction-post-model-review-development-v1.md"
MATERIAL_NAME = "disagreement-review-material.json"
LOOPBACK = "127.0.0.1"
CONTEXT_CHARS = 300
NOTE_OVERLAP_CHARS = 40


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def load(path: pathlib.Path) -> Any:
    return json.loads(path.read_text("utf-8"))


def dump(doc: Any) -> bytes:
    return (json.dumps(doc, indent=1, ensure_ascii=False) + "\n").encode("utf-8")


def outside_repository(path: pathlib.Path) -> bool:
    return not path.resolve().is_relative_to(ROOT.resolve())


def label_definition() -> dict[str, str]:
    """The frozen wording in effect during the run, quoted from the repository, never re-written."""
    label = next(item for item in LABELS if item.label_id == LABEL)
    prompt = PROMPT_SOURCE.read_text("utf-8")
    start = prompt.index("REPORTED_FAILED_ATTEMPT\nThe asker")
    end = prompt.index("\n\nNEGATIVE_EVALUATION_OF_NAMED_SOLUTION\n", start)
    never_start = prompt.index("WHAT NEVER COUNTS")
    never_end = prompt.index("\n\nHOW TO ANSWER", never_start)
    return {
        "label_set": f"{LABEL_SET_ID}@{LABEL_SET_VERSION}",
        "label_set_definition": label.definition,
        "prompt": "first-person-semantic-extraction-prompt@1.0.0",
        "prompt_definition": prompt[start:end],
        "prompt_what_never_counts": prompt[never_start:never_end],
        "annotation_holder_rule": load(CONTRACT)["evaluation_protocol"]["annotation"][
            "holder_rule"
        ],
    }


def review_inputs() -> tuple[dict[str, str], list[dict[str, str]], dict[str, list[dict[str, Any]]]]:
    """Bindings and the exact review set, from committed artifacts only."""
    summary = load(SUMMARY)
    annotation = load(ANNOTATION)
    evaluation = load(EVALUATION)
    packet = load(PACKET)
    reference = {r["normalized_record_id"]: r for r in annotation["records"]}
    records, findings = [], {}
    for record in sorted(summary["records"], key=lambda r: r["normalized_record_id"]):
        extraction = record.get("extraction")
        if not record["accepted"] or extraction is None:
            continue
        mine = [f for f in extraction["findings"] if f["finding_type"] == LABEL]
        blind = reference[record["normalized_record_id"]]["labels"][LABEL]["state"]
        if mine and blind == "ABSENT":
            rid = record["normalized_record_id"]
            findings[rid] = mine
            records.append(
                {
                    "normalized_record_id": rid,
                    "surface_sha256": record["surface_sha256"],
                    "original_blind_state": blind,
                    "model_state": "PRESENT",
                    "model_findings_sha256": findings_digest(mine),
                }
            )
    reported = evaluation["labels"][LABEL]["disagreements"]["model_PRESENT_reference_ABSENT"]
    if [r["normalized_record_id"] for r in records] != sorted(reported):
        raise SystemExit("REFUSED  the derived review set differs from the committed evaluation")
    bindings = {
        "packet_sha256": packet["packet_sha256"],
        "approval_sha256": sha(APPROVAL.read_bytes()),
        "run_summary_sha256": sha(SUMMARY.read_bytes()),
        "pilot_evaluation_sha256": sha(EVALUATION.read_bytes()),
        "original_annotation_sha256": sha(ANNOTATION.read_bytes()),
        "label_definition": f"{LABEL_SET_ID}@{LABEL_SET_VERSION}",
        "label_definition_sha256": canonical_sha256(label_definition()),
        "prompt_sha256": packet["prompt"]["sha256"],
    }
    if (
        summary["packet_sha256"] != bindings["packet_sha256"]
        or summary.get("approval_sha256") != bindings["approval_sha256"]
    ):
        raise SystemExit("REFUSED  the run summary does not name the committed packet and approval")
    return bindings, records, findings


def material_record(
    position: int,
    record: dict[str, str],
    surface: str,
    findings: list[dict[str, Any]],
    note_present: bool,
) -> dict[str, Any]:
    if surface_sha256(surface) != record["surface_sha256"]:
        raise SystemExit(
            f"REFUSED  surface {record['normalized_record_id']} does not match its digest"
        )
    rebuilt = []
    for finding in sorted(findings, key=lambda f: f["evidence_start"]):
        start, end = finding["evidence_start"], finding["evidence_end"]
        quote = surface[start:end]
        if sha(quote.encode("utf-8")) != finding["evidence_sha256"]:
            raise SystemExit(
                f"REFUSED  a model quote for {record['normalized_record_id']} no longer matches"
            )
        rebuilt.append(
            {
                "finding_id": finding["finding_id"],
                "evidence_start": start,
                "evidence_end": end,
                "quote": quote,
                "before": surface[max(0, start - CONTEXT_CHARS) : start],
                "after": surface[end : end + CONTEXT_CHARS],
                "line": surface.count("\n", 0, start) + 1,
            }
        )
    return {
        **record,
        "position": position,
        "surface": surface,
        "surface_length": len(surface),
        "original_note_present": note_present,
        "findings": rebuilt,
    }


def prepare(out: pathlib.Path, operator_id: str) -> int:
    if not outside_repository(out):
        print("REFUSED  review material holds exact source text; it lives outside the repository")
        return 1
    bindings, records, findings = review_inputs()
    try:
        working = blank_working_file(operator_id, bindings, records)
    except ReviewRefusedError as exc:
        print(f"REFUSED  {exc}")
        return 1
    target = out / f"post-model-review-working-{operator_id}.json"
    if target.exists():
        print(f"REFUSED  {target} exists; a working file is never overwritten (serve it to resume)")
        return 1
    from build_semantic_egress_eligibility import development_surfaces

    surfaces = development_surfaces()
    reference = {r["normalized_record_id"]: r for r in load(ANNOTATION)["records"]}
    material = {
        "$comment": "LOCAL POST-MODEL REVIEW MATERIAL. Exact DEVELOPMENT surfaces and model quotes. Never commit, never upload.",
        "bindings": bindings,
        "label_definition": label_definition(),
        "records": [
            material_record(
                i,
                r,
                surfaces[r["normalized_record_id"]],
                findings[r["normalized_record_id"]],
                reference[r["normalized_record_id"]]["labels"][LABEL]["note_present"],
            )
            for i, r in enumerate(records, 1)
        ],
    }
    out.mkdir(parents=True, exist_ok=True)
    (out / MATERIAL_NAME).write_bytes(dump(material))
    target.write_bytes(dump(working))
    print(f"prepared {len(records)} disagreement records for {operator_id} in {out}")
    return 0


class ReviewSession:
    """State behind the local page. Every mutation comes from one explicit POST and is saved at once."""

    def __init__(self, folder: pathlib.Path) -> None:
        self.material = load(folder / MATERIAL_NAME)
        workings = sorted(folder.glob("post-model-review-working-*.json"))
        if len(workings) != 1:
            raise SystemExit("REFUSED  the folder must hold exactly one working file")
        self.working_path = workings[0]
        self.working = load(self.working_path)
        if self.working["bindings"] != self.material["bindings"]:
            raise SystemExit(
                "REFUSED  the working file and the material were prepared from different inputs"
            )
        self.records = {r["normalized_record_id"]: r for r in self.material["records"]}
        if set(self.records) != {r["normalized_record_id"] for r in self.working["records"]}:
            raise SystemExit("REFUSED  the working file and the material list different records")
        for record in self.records.values():
            if surface_sha256(record["surface"]) != record["surface_sha256"]:
                raise SystemExit(
                    f"REFUSED  local surface {record['normalized_record_id']} was altered"
                )
        self.token = secrets.token_urlsafe(32)

    def save(self) -> None:
        temporary = self.working_path.with_suffix(".json.tmp")
        temporary.write_bytes(dump(self.working))
        temporary.replace(self.working_path)

    def state(self) -> dict[str, Any]:
        decided = {d["normalized_record_id"]: d for d in self.working["decisions"]}
        return {
            "operator_id": self.working["operator_id"],
            "provenance": PROVENANCE,
            "total": len(self.records),
            "decided": len(decided),
            "unresolved": sum(1 for d in decided.values() if d["decision"] == UNRESOLVED),
            "choices": list(CHOICES),
            "note_required": sorted(NOTE_REQUIRED),
            "label_definition": self.material["label_definition"],
            "records": [
                {**record, "decision": decided.get(rid)}
                for rid, record in sorted(self.records.items(), key=lambda kv: kv[1]["position"])
            ],
        }

    def decide(self, body: dict[str, Any]) -> None:
        rid = str(body.get("normalized_record_id"))
        if rid not in self.records:
            raise ReviewRefusedError("RECORD_NOT_UNDER_REVIEW", rid)
        note = str(body.get("note") or "")
        if overlaps_source(note, self.records[rid]["surface"]):
            raise ReviewRefusedError(
                "NOTE_QUOTES_SOURCE_TEXT",
                "describe the reason in your own words; do not paste the question",
            )
        decision = make_decision(
            self.working,
            rid,
            surface_sha256=str(body.get("surface_sha256")),
            model_findings_sha256=str(body.get("model_findings_sha256")),
            choice=str(body.get("decision")),
            note=note,
            decided_at=datetime.now().astimezone().isoformat(timespec="seconds"),
        )
        self.working["decisions"] = [
            d for d in self.working["decisions"] if d["normalized_record_id"] != rid
        ] + [decision]
        self.save()

    def undo(self, body: dict[str, Any]) -> None:
        rid = str(body.get("normalized_record_id"))
        self.working["decisions"] = [
            d for d in self.working["decisions"] if d["normalized_record_id"] != rid
        ]
        self.save()


def overlaps_source(note: str, surface: str, width: int = NOTE_OVERLAP_CHARS) -> bool:
    """True when the note repeats at least `width` consecutive characters of the question text."""
    text = " ".join(note.split())
    flat = " ".join(surface.split())
    return any(text[i : i + width] in flat for i in range(0, max(0, len(text) - width + 1)))


PAGE = """<!doctype html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Post-model disagreement review</title>
<style nonce="__NONCE__">
:root{--bg:#fafaf7;--fg:#1d1d1b;--muted:#6b6b66;--line:#d9d7cf;--card:#fff;--hit:#cfe3ff;--hitline:#2d4f8a;--blind:#a62b2b;--accent:#2d4f8a}
@media (prefers-color-scheme:dark){:root{--bg:#161614;--fg:#ecebe6;--muted:#a3a29b;--line:#3a3934;--card:#1f1f1c;--hit:#1f3558;--hitline:#8fb0e8;--blind:#e07a7a;--accent:#8fb0e8}}
*{box-sizing:border-box}body{margin:0;background:var(--bg);color:var(--fg);font:15px/1.5 system-ui,sans-serif}
header{position:sticky;top:0;background:var(--bg);border-bottom:1px solid var(--line);padding:10px 16px;display:flex;gap:12px;align-items:center;flex-wrap:wrap;z-index:2}
main{max-width:1100px;margin:0 auto;padding:16px}
button{font:inherit;padding:6px 10px;border:1px solid var(--line);background:var(--card);color:var(--fg);border-radius:6px;cursor:pointer}
.card{background:var(--card);border:1px solid var(--line);border-radius:8px;padding:14px;margin:12px 0}
.blind{border:2px solid var(--blind)}.blind h3{color:var(--blind);margin:0 0 6px}
.muted{color:var(--muted)}.mono{font-family:ui-monospace,Consolas,monospace}
pre{white-space:pre-wrap;word-break:break-word;margin:0}
pre.surface{border:1px solid var(--line);border-radius:6px;padding:12px;max-height:55vh;overflow:auto}
mark{background:var(--hit);color:inherit;outline:1px solid var(--hitline)}
textarea{width:100%;min-height:70px;font:inherit}.row{display:flex;gap:8px;flex-wrap:wrap;margin:8px 0}
.banner{padding:8px 10px;border-radius:6px;border:1px solid var(--hitline);margin:8px 0}.error{border-color:var(--blind);color:var(--blind)}
</style></head><body>
<header><strong>Post-model review: REPORTED_FAILED_ATTEMPT disagreements</strong><span id="progress" class="muted"></span>
<button id="prev">&larr; Previous</button><button id="next">Next &rarr;</button><button id="nextOpen">Next undecided</button></header>
<main><div class="banner">POST_MODEL_OPERATOR_REVIEW. You are seeing the model's answer, so this is NOT a blind annotation. It never edits or replaces your original blind reference, and the Mission 1.85.9 results stay as they were. Nothing is chosen until you click.</div>
<div id="error" class="banner error" hidden></div><div id="view"></div>
<p class="muted">Local page on 127.0.0.1. It loads nothing from the internet and sends nothing anywhere but this local server.</p></main>
<script nonce="__NONCE__">
const TOKEN="__TOKEN__";let S=null,i=0;
const $=id=>document.getElementById(id);
function el(tag,attrs,...kids){const e=document.createElement(tag);for(const[k,v]of Object.entries(attrs||{})){if(k==="class")e.className=v;else if(k==="onclick")e.addEventListener("click",v);else e.setAttribute(k,v)}for(const k of kids)e.append(k);return e}
async function load(){const r=await fetch("/api/state",{headers:{"X-Review-Token":TOKEN}});S=await r.json();render()}
async function post(path,body){$("error").hidden=true;const r=await fetch(path,{method:"POST",headers:{"Content-Type":"application/json","X-Review-Token":TOKEN},body:JSON.stringify(body)});const j=await r.json();if(!r.ok){$("error").textContent="Refused: "+j.error;$("error").hidden=false}S=j.state||S;render()}
function render(){$("progress").textContent=S.decided+" / "+S.total+" with a choice ("+S.unresolved+" UNRESOLVED), operator "+S.operator_id;
 const r=S.records[i],v=$("view");v.replaceChildren();
 v.append(el("div",{class:"card"},el("strong",{},r.position+" / "+S.total+"  "),el("span",{class:"mono"},r.normalized_record_id),el("div",{class:"muted mono"},"surface_sha256 "+r.surface_sha256.slice(0,16)+"...  model_findings_sha256 "+r.model_findings_sha256.slice(0,16)+"...")));
 if(r.decision)v.append(el("div",{class:"banner"},"Your choice: "+r.decision.decision+(r.decision.operator_note?" | note: "+r.decision.operator_note:"")+" ("+r.decision.decided_at+") ",el("button",{onclick:()=>post("/api/undo",{normalized_record_id:r.normalized_record_id})},"Undo")));
 v.append(el("div",{class:"card blind"},el("h3",{},"BLIND HUMAN REFERENCE \\u2014 DO NOT EDIT"),el("div",{class:"mono"},"REPORTED_FAILED_ATTEMPT = "+r.original_blind_state),el("div",{class:"muted"},r.original_note_present?"You wrote a note at the time; its text was kept in your local annotation working file and is not in the repository.":"No note was recorded with this label."),el("div",{class:"muted"},"This page cannot change it.")));
 const m=el("div",{class:"card"},el("h3",{},"Model result"),el("div",{class:"mono"},"REPORTED_FAILED_ATTEMPT = "+r.model_state+"  ("+r.findings.length+" accepted quote"+(r.findings.length>1?"s":"")+")"));
 for(const f of r.findings){m.append(el("div",{class:"card"},el("div",{class:"muted mono"},"offsets "+f.evidence_start+"\\u2013"+f.evidence_end+", line "+f.line),el("pre",{class:"mono"},f.before,el("mark",{},f.quote),f.after)))}
 v.append(m);
 const pre=el("pre",{class:"surface mono"});let pos=0;for(const f of r.findings){if(f.evidence_start<pos)continue;pre.append(document.createTextNode(r.surface.slice(pos,f.evidence_start)),el("mark",{},r.surface.slice(f.evidence_start,f.evidence_end)));pos=f.evidence_end}pre.append(document.createTextNode(r.surface.slice(pos)));
 v.append(el("div",{class:"card"},el("strong",{},"Complete question surface (frozen, unaltered; highlights are the model's quotes)"),pre));
 const d=S.label_definition;
 v.append(el("div",{class:"card"},el("h3",{},"Frozen definition in effect during the run"),el("div",{class:"muted"},d.label_set+" and "+d.prompt),el("pre",{},d.label_set_definition),el("pre",{class:"muted"},"\\nPrompt wording:\\n"+d.prompt_definition+"\\n\\n"+d.prompt_what_never_counts+"\\n\\nAnnotation holder rule: "+d.annotation_holder_rule)));
 const note=el("textarea",{placeholder:"Your reason in your own words (required for POST_MODEL_HUMAN_REVISION and LABEL_DEFINITION_AMBIGUOUS). Do not paste the question text."});
 const row=el("div",{class:"row"});
 for(const c of S.choices){row.append(el("button",{onclick:()=>post("/api/decide",{normalized_record_id:r.normalized_record_id,surface_sha256:r.surface_sha256,model_findings_sha256:r.model_findings_sha256,decision:c,note:note.value})},c))}
 v.append(el("div",{class:"card"},el("h3",{},"Your choice for this record"),el("ul",{},
  el("li",{},"HUMAN_REFERENCE_CONFIRMED_MODEL_OVERREAD: after seeing the model's evidence, ABSENT is still correct under the frozen definition."),
  el("li",{},"POST_MODEL_HUMAN_REVISION: after seeing it, you now judge the text should have been PRESENT (note required). The blind reference is not changed."),
  el("li",{},"LABEL_DEFINITION_AMBIGUOUS: a reasonable reading of the frozen definition allows either answer (note required)."),
  el("li",{},"UNRESOLVED: leave it open for now; the review cannot be complete while any record is unresolved.")),note,row))}
$("prev").addEventListener("click",()=>{i=Math.max(0,i-1);render()});
$("next").addEventListener("click",()=>{i=Math.min(S.total-1,i+1);render()});
$("nextOpen").addEventListener("click",()=>{const n=S.records.findIndex((r,k)=>k>i&&(!r.decision||r.decision.decision==="UNRESOLVED"));const f=n>=0?n:S.records.findIndex(r=>!r.decision||r.decision.decision==="UNRESOLVED");if(f>=0)i=f;render()});
load();
</script></body></html>"""


def make_handler(
    session: ReviewSession, port_holder: dict[str, int]
) -> type[http.server.BaseHTTPRequestHandler]:
    nonce = secrets.token_urlsafe(16)

    class Handler(http.server.BaseHTTPRequestHandler):
        server_version = "post-model-review"

        def log_message(self, format: str, *args: Any) -> None:  # noqa: A002 - stdlib signature
            return  # nothing is logged: bodies name records and choices

        def _host_ok(self) -> bool:
            port = port_holder["port"]
            return self.headers.get("Host") in {f"{LOOPBACK}:{port}", f"localhost:{port}"}

        def _send(self, status: int, body: bytes, content_type: str) -> None:
            self.send_response(status)
            self.send_header("Content-Type", content_type)
            self.send_header("Content-Length", str(len(body)))
            self.send_header("Cache-Control", "no-store")
            self.send_header("Referrer-Policy", "no-referrer")
            self.send_header("X-Content-Type-Options", "nosniff")
            self.send_header(
                "Content-Security-Policy",
                f"default-src 'none'; script-src 'nonce-{nonce}'; style-src 'nonce-{nonce}'; "
                "connect-src 'self'; img-src 'none'; base-uri 'none'; form-action 'none'; "
                "frame-ancestors 'none'",
            )
            self.end_headers()
            self.wfile.write(body)

        def _json(self, status: int, doc: Any) -> None:
            self._send(
                status, json.dumps(doc, ensure_ascii=False).encode("utf-8"), "application/json"
            )

        def do_GET(self) -> None:  # noqa: N802 - stdlib name
            if not self._host_ok():
                return self._json(421, {"error": "HOST_NOT_LOOPBACK"})
            if self.path == "/":
                page = PAGE.replace("__NONCE__", nonce).replace(
                    "__TOKEN__", html.escape(session.token)
                )
                return self._send(200, page.encode("utf-8"), "text/html; charset=utf-8")
            if self.path == "/api/state":
                if self.headers.get("X-Review-Token") != session.token:
                    return self._json(403, {"error": "TOKEN_REQUIRED"})
                return self._json(200, session.state())
            return self._json(404, {"error": "NOT_FOUND"})

        def do_POST(self) -> None:  # noqa: N802 - stdlib name
            # Read the bounded body before any answer, so a refusal is never lost to a connection reset.
            length = int(self.headers.get("Content-Length") or 0)
            raw = self.rfile.read(min(length, 100_000))
            if not self._host_ok():
                return self._json(421, {"error": "HOST_NOT_LOOPBACK"})
            if self.headers.get("X-Review-Token") != session.token:
                return self._json(403, {"error": "TOKEN_REQUIRED"})
            if self.headers.get("Content-Type") != "application/json":
                return self._json(415, {"error": "JSON_REQUIRED"})
            action = {"/api/decide": session.decide, "/api/undo": session.undo}.get(self.path)
            if action is None:
                return self._json(404, {"error": "NOT_FOUND"})
            try:
                body = json.loads(raw.decode("utf-8") or "{}")
                action(body if isinstance(body, dict) else {})
            except ReviewRefusedError as exc:
                return self._json(422, {"error": str(exc), "state": session.state()})
            except ValueError:
                return self._json(400, {"error": "BAD_REQUEST"})
            return self._json(200, {"state": session.state()})

    return Handler


def build_server(
    folder: pathlib.Path, port: int
) -> tuple[http.server.ThreadingHTTPServer, ReviewSession]:
    session = ReviewSession(folder)
    port_holder = {"port": port}
    server = http.server.ThreadingHTTPServer((LOOPBACK, port), make_handler(session, port_holder))
    port_holder["port"] = server.server_address[1]
    return server, session


def serve(folder: pathlib.Path, port: int) -> int:
    if not outside_repository(folder):
        print("REFUSED  review material lives outside the repository")
        return 1
    server, session = build_server(folder, port)
    print(
        f"Post-model review for {session.working['operator_id']}: open http://{LOOPBACK}:{server.server_address[1]}/"
    )
    print("Every click is saved immediately. Stop with Ctrl+C and run the same command to resume.")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nstopped; choices so far are saved")
    finally:
        server.server_close()
    return 0


def _surfaces_for(records: list[dict[str, str]]) -> dict[str, str]:
    from build_semantic_egress_eligibility import development_surfaces

    surfaces = development_surfaces()
    return {r["normalized_record_id"]: surfaces[r["normalized_record_id"]] for r in records}


def _problems(working: dict[str, Any]) -> list[tuple[str, str]]:
    bindings, records, _ = review_inputs()
    problems = validate_working(working, expected_bindings=bindings, expected_records=records)
    surfaces = _surfaces_for(records)
    for decision in working.get("decisions", []):
        rid = decision.get("normalized_record_id")
        if rid in surfaces and overlaps_source(
            str(decision.get("operator_note") or ""), surfaces[rid]
        ):
            problems.append(("NOTE_QUOTES_SOURCE_TEXT", str(rid)))
    return problems


def lint(path: pathlib.Path) -> int:
    working = load(path)
    problems = _problems(working)
    for code, detail in problems:
        print(f"{code:48} {detail}")
    status = review_status(working, problems)
    print(
        f"status   {status}; {len(working['decisions'])} of {len(working['records'])} records carry a choice"
    )
    return 1 if problems else 0


def diagnostic(
    counts: dict[str, int], present_calls: int, blind_false_present: int
) -> dict[str, Any]:
    sys.path.insert(0, str(ROOT / "infrastructure/scripts"))
    from evaluate_semantic_extraction_pilot import clopper_pearson_upper

    reclassified = blind_false_present - counts[REVISION]
    excluded = present_calls - counts[AMBIGUOUS]
    overread_only = counts[OVERREAD]
    return {
        "name": "POST_MODEL_REVIEW_DIAGNOSTIC",
        "post_hoc": True,
        "preregistered": False,
        "is_the_mission_1_85_9_gate_result": False,
        "certification": False,
        "reads": "false PRESENT on REPORTED_FAILED_ATTEMPT if post-model revisions are counted as PRESENT",
        "ambiguous_counted_as_false_present": {
            "false_present": reclassified,
            "present_calls": present_calls,
            "point_estimate": round(reclassified / present_calls, 6),
            "clopper_pearson_upper_95": clopper_pearson_upper(reclassified, present_calls),
        },
        "ambiguous_excluded": {
            "false_present": overread_only,
            "present_calls": excluded,
            "point_estimate": round(overread_only / excluded, 6) if excluded else None,
            "clopper_pearson_upper_95": clopper_pearson_upper(overread_only, excluded)
            if excluded
            else None,
        },
    }


def render_review(
    working: dict[str, Any], problems: list[tuple[str, str]]
) -> tuple[dict[str, Any], bytes]:
    status = review_status(working, problems)
    analysis = analyse(working, status)
    evaluation = load(EVALUATION)
    label = evaluation["labels"][LABEL]
    gate = next(
        r for r in evaluation["readings"] if r["item_id"] == f"false_present_rate_upper_95::{LABEL}"
    )
    doc = {
        "$comment": "POST-MODEL OPERATOR REVIEW (Mission 1.85.10). The operator saw the model's disagreement before choosing: this is NOT a blind annotation, does not replace the original reference (left byte-for-byte unchanged), may inform a later prompt, contract or label-definition decision, and leaves the preregistered Mission 1.85.9 readings unchanged. Bounded metadata only: no question text, no model quote.",
        "review_id": REVIEW_ID,
        "version": "1.0.0",
        "provenance": PROVENANCE,
        "blind": False,
        "replaces_original_reference": False,
        "label": LABEL,
        "operator_id": working["operator_id"],
        "bindings": working["bindings"],
        "records": working["records"],
        "decisions": sorted(working["decisions"], key=lambda d: d["normalized_record_id"]),
        "analysis": analysis,
        "mission_1_85_9_gate_unchanged": {
            "item_id": gate["item_id"],
            "reading": gate["reading"],
            "false_present": gate["false_present"],
            "present_calls": gate["support"]["present_calls_on_decided_records"],
            "clopper_pearson_upper_95": gate["clopper_pearson_upper_95_one_sided"],
            "reference": "the original blind SINGLE_HUMAN_REFERENCE",
        },
        "post_model_review_diagnostic": (
            diagnostic(
                analysis["counts"],
                gate["support"]["present_calls_on_decided_records"],
                label["false_present"],
            )
            if status == "COMPLETE"
            else None
        ),
    }
    counts = analysis["counts"]
    lines = [
        "# Post-model operator review of the REPORTED_FAILED_ATTEMPT disagreements (v1)",
        "",
        "> Generated by `infrastructure/scripts/semantic_disagreement_review.py import`. Do not edit by hand.",
        "",
        "`POST_MODEL_OPERATOR_REVIEW`: not a blind annotation, never a replacement for the original reference. The Mission 1.85.9 reading stays "
        f"`{gate['reading']}` ({gate['false_present']} of {gate['support']['present_calls_on_decided_records']}, upper {gate['clopper_pearson_upper_95_one_sided']}).",
        "",
        f"Status `{status}`, operator `{working['operator_id']}`.",
        "",
        "```text",
        *(f"{name:40} = {counts[name]}" for name in (OVERREAD, REVISION, AMBIGUOUS, UNRESOLVED)),
        f"{'UNDECIDED':40} = {analysis['undecided']}",
        "```",
        "",
        "Development recommendations: "
        + (
            ", ".join(f"`{r}`" for r in analysis["development_recommendations"])
            or "none derived (review not complete)"
        )
        + ". Nothing is revised automatically.",
        "",
        "| Record | Blind reference | Model | Post-model choice | Decided at |",
        "|---|---|---|---|---|",
    ]
    decided = {d["normalized_record_id"]: d for d in working["decisions"]}
    for record in working["records"]:
        d = decided.get(record["normalized_record_id"])
        lines.append(
            f"| `{record['normalized_record_id']}` | {record['original_blind_state']} | {record['model_state']} | "
            f"{d['decision'] if d else 'undecided'} | {d['decided_at'] if d else ''} |"
        )
    lines.append("")
    return doc, "\n".join(lines).encode("utf-8")


def import_review(path: pathlib.Path) -> int:
    working = load(path)
    problems = _problems(working)
    if problems:
        for code, detail in problems:
            print(f"{code:48} {detail}")
        print("REFUSED  nothing was imported")
        return 1
    if len(working["decisions"]) != len(working["records"]):
        print(
            f"REFUSED  {len(working['records']) - len(working['decisions'])} record(s) carry no choice yet"
        )
        return 1
    doc, page = render_review(working, problems)
    REVIEW.write_bytes(dump(doc))
    REVIEW_PAGE.write_bytes(page)
    print(
        f"imported {len(working['decisions'])} post-model choices; status {doc['analysis']['status']}"
    )
    return 0


def check() -> int:
    if not REVIEW.exists():
        print("ok       no post-model review recorded yet (WAITING_FOR_POST_MODEL_OPERATOR_REVIEW)")
        return 0
    doc = load(REVIEW)
    bindings, records, _ = review_inputs()
    problems = validate_working(doc, expected_bindings=bindings, expected_records=records)
    if doc.get("blind") is not False or doc.get("replaces_original_reference") is not False:
        problems.append(("POST_MODEL_REVIEW_CLAIMS_TO_BE_BLIND", REVIEW.name))
    rebuilt, page = render_review(doc, [])
    if problems or dump(rebuilt) != REVIEW.read_bytes() or page != REVIEW_PAGE.read_bytes():
        for code, detail in problems:
            print(f"FAIL     {code} {detail}")
        print(f"FAIL     {REVIEW.name} is stale or not reproducible")
        return 1
    print(f"ok       {REVIEW.name} matches (status {doc['analysis']['status']})")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    sub = parser.add_subparsers(dest="command", required=True)
    p = sub.add_parser("prepare")
    p.add_argument("--out", required=True)
    p.add_argument("--operator-id", required=True)
    s = sub.add_parser("serve")
    s.add_argument("folder")
    s.add_argument("--port", type=int, default=8766)
    sub.add_parser("lint").add_argument("working")
    sub.add_parser("import").add_argument("working")
    sub.add_parser("check")
    args = parser.parse_args(argv)
    for stream in (sys.stdout, sys.stderr):
        reconfigure = getattr(stream, "reconfigure", None)
        if reconfigure is not None:
            reconfigure(encoding="utf-8")
    if args.command == "prepare":
        return prepare(pathlib.Path(args.out), args.operator_id)
    if args.command == "serve":
        return serve(pathlib.Path(args.folder), args.port)
    if args.command == "lint":
        return lint(pathlib.Path(args.working))
    if args.command == "import":
        return import_review(pathlib.Path(args.working))
    return check()


if __name__ == "__main__":
    sys.exit(main())
