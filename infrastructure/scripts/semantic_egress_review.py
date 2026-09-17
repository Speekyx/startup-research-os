"""Mission 1.85.6 (N08-B-PILOT). Local human egress review for the DEVELOPMENT split.

Policy REVIEW_OR_EXCLUDE_NO_REDACTION, defined in `sros_semantic_extraction_contract.egress` and not
redefined here. This tool makes NO egress decision. It shows the operator each record that still needs
review, with the exact surface that would be transmitted and every review trigger, and records only
the choices the operator clicks.

    prepare  --out DIR --operator-id ID
             Render the reviewable DEVELOPMENT surfaces and their triggers into DIR (outside the
             repository) with an empty working decision file. Reads the held records (DATABASE_URL).
    serve    DIR [--port N]
             A local review page on 127.0.0.1 only. No database, no network beyond loopback, no
             external asset. Every click is saved to the working file at once; closing and serving
             again resumes.
    lint     WORKING
             Validate the working file against a freshly computed scan. Prints every problem. Writes
             nothing. Reads the held records (DATABASE_URL).
    import   WORKING
             Refuse unless valid and complete, then write the canonical decision document, rebuild
             the scan and eligibility, and re-render the evaluation packet.

No path here calls a model or a provider, and no Stack Overflow text leaves the machine.
"""

from __future__ import annotations

import argparse
import html
import http.server
import json
import pathlib
import secrets
import sys
from typing import Any

ROOT = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "packages/semantic-extraction-contract/python"))
sys.path.insert(0, str(ROOT / "infrastructure/scripts"))

from sros_semantic_extraction_contract.egress import scan_surface  # noqa: E402
from sros_semantic_extraction_contract.egress_review import (  # noqa: E402
    CONFIRMATION,
    EXCLUDING_REASONS,
    INDIVIDUAL_APPROVING_REASONS,
    ChoiceRefusedError,
    blank_working_file,
    check_operator,
    committed_decisions,
    make_bulk_decision,
    make_decision,
    record_set_sha256,
    reviewable_records,
    unresolved_record_ids,
    validate_working_decisions,
    zero_trigger_unresolved_ids,
)
from sros_semantic_extraction_contract.surface import surface_sha256  # noqa: E402

DATA = ROOT / "docs" / "data"
DECISIONS = DATA / "stack-overflow-semantic-egress-decisions-development-v1.json"
CORPUS = DATA / "stack-overflow-semantic-evaluation-corpus-v1.json"
MATERIAL_NAME = "review-material.json"
LOOPBACK = "127.0.0.1"
CONTEXT_CHARS = 60


def dump(doc: Any) -> bytes:
    return (json.dumps(doc, indent=1, ensure_ascii=False) + "\n").encode("utf-8")


def working_name(operator_id: str) -> str:
    return f"egress-decisions-working-{operator_id}.json"


def outside_repository(path: pathlib.Path) -> bool:
    return not path.resolve().is_relative_to(ROOT.resolve())


def current_scan() -> tuple[dict[str, Any], dict[str, str]]:
    """The scan computed now from the held records, and the surfaces. Needs DATABASE_URL."""
    from build_semantic_egress_eligibility import build, development_surfaces

    surfaces = development_surfaces()
    scan, _ = build(surfaces, json.loads(DECISIONS.read_text("utf-8")))
    return scan, surfaces


def holdout_ids() -> set[str]:
    corpus = json.loads(CORPUS.read_text("utf-8"))
    return {r["normalized_record_id"] for r in corpus["records"] if r["split"] == "HOLDOUT"}


def segments(surface: str) -> list[dict[str, Any]]:
    """The surface cut at every trigger boundary. Joining the texts gives the surface back exactly."""
    spans = [(a, b, name) for name, found in scan_surface(surface).items() for a, b in found]
    cuts = sorted({0, len(surface), *(a for a, _, _ in spans), *(b for _, b, _ in spans)})
    out = []
    for start, end in zip(cuts, cuts[1:], strict=False):
        names = sorted({n for a, b, n in spans if a <= start and end <= b})
        out.append({"text": surface[start:end], "patterns": names})
    return out


def material_record(position: int, record: dict[str, Any], surface: str) -> dict[str, Any]:
    triggers = [
        {
            "pattern": name,
            "text": surface[a:b],
            "before": surface[max(0, a - CONTEXT_CHARS) : a],
            "after": surface[b : b + CONTEXT_CHARS],
            "line": surface.count("\n", 0, a) + 1,
        }
        for name, found in scan_surface(surface).items()
        for a, b in found
    ]
    return {
        "position": position,
        "normalized_record_id": record["normalized_record_id"],
        "surface_sha256": record["surface_sha256"],
        "trigger_counts": record["trigger_counts"],
        "transmission_problems": record["transmission_problems"],
        "surface": surface,
        "surface_length": len(surface),
        "triggers": triggers,
        "segments": segments(surface),
    }


def prepare(out: pathlib.Path, operator_id: str) -> int:
    if not outside_repository(out):
        print(
            "REFUSED  review material holds exact source surfaces; it lives outside the repository"
        )
        return 1
    scan, surfaces = current_scan()
    reviewable = reviewable_records(scan["records"], json.loads(DECISIONS.read_text("utf-8")))
    working = blank_working_file(operator_id, reviewable, scan["scan_sha256"])
    try:
        check_operator(operator_id)
    except ChoiceRefusedError as exc:
        print(f"REFUSED  {exc}")
        return 1
    target = out / working_name(operator_id)
    if target.exists():
        print(f"REFUSED  {target} exists; a working file is never overwritten (serve it to resume)")
        return 1
    material = {
        "$comment": "LOCAL REVIEW MATERIAL. Exact DEVELOPMENT surfaces and trigger matches. Never commit, never upload.",
        "split": "DEVELOPMENT",
        "scan_sha256": scan["scan_sha256"],
        "records": [
            material_record(i, r, surfaces[r["normalized_record_id"]])
            for i, r in enumerate(sorted(reviewable, key=lambda r: r["normalized_record_id"]), 1)
        ],
    }
    out.mkdir(parents=True, exist_ok=True)
    (out / MATERIAL_NAME).write_bytes(dump(material))
    target.write_bytes(dump(working))
    zero = sum(1 for r in reviewable if not any(r["trigger_counts"].values()))
    print(
        f"prepared {len(reviewable)} records for {operator_id} in {out} "
        f"({len(reviewable) - zero} with triggers, {zero} without)"
    )
    return 0


class ReviewSession:
    """State behind the local page. Every mutation comes from one explicit POST and is saved at once."""

    def __init__(self, folder: pathlib.Path) -> None:
        self.folder = folder
        self.material = json.loads((folder / MATERIAL_NAME).read_text("utf-8"))
        workings = sorted(folder.glob("egress-decisions-working-*.json"))
        if len(workings) != 1:
            raise SystemExit("REFUSED  the folder must hold exactly one working decision file")
        self.working_path = workings[0]
        self.working = json.loads(self.working_path.read_text("utf-8"))
        if self.working.get("prepared_from_scan_sha256") != self.material.get("scan_sha256"):
            raise SystemExit(
                "REFUSED  the working file and the review material come from different scans"
            )
        self.records = {r["normalized_record_id"]: r for r in self.material["records"]}
        for record in self.records.values():
            if surface_sha256(record["surface"]) != record["surface_sha256"]:
                raise SystemExit(
                    f"REFUSED  local surface {record['normalized_record_id']} does not match its digest"
                )
        self.token = secrets.token_urlsafe(32)

    def save(self) -> None:
        temporary = self.working_path.with_suffix(".json.tmp")
        temporary.write_bytes(dump(self.working))
        temporary.replace(self.working_path)

    def state(self) -> dict[str, Any]:
        individual = {d["normalized_record_id"]: d for d in self.working["decisions"]}
        in_bulk = {
            rid: b["bulk_decision_id"]
            for b in self.working["bulk_decisions"]
            for rid in b["normalized_record_ids"]
        }
        rows = []
        for rid in sorted(self.records, key=lambda r: self.records[r]["position"]):
            record = self.records[rid]
            decision = individual.get(rid)
            stale = decision is not None and decision["surface_sha256"] != record["surface_sha256"]
            rows.append(
                {
                    **{
                        k: record[k]
                        for k in (
                            "position",
                            "normalized_record_id",
                            "surface_sha256",
                            "surface_length",
                            "triggers",
                            "segments",
                        )
                    },
                    "trigger_summary": {k: v for k, v in record["trigger_counts"].items() if v},
                    "decision": None if stale else decision,
                    "stale_decision": decision if stale else None,
                    "bulk_decision_id": in_bulk.get(rid),
                }
            )
        zero = zero_trigger_unresolved_ids(self.working, self.records)
        return {
            "operator_id": self.working["operator_id"],
            "total": len(rows),
            "unresolved": len(unresolved_record_ids(self.working)),
            "records": rows,
            "approving_reasons": list(INDIVIDUAL_APPROVING_REASONS),
            "excluding_reasons": list(EXCLUDING_REASONS),
            "bulk_decisions": self.working["bulk_decisions"],
            "zero_trigger_set": {
                "normalized_record_ids": zero,
                "surface_sha256": {rid: self.records[rid]["surface_sha256"] for rid in zero},
                "record_set_sha256": record_set_sha256(zero) if zero else None,
                "confirmation": CONFIRMATION.format(n=len(zero)),
            },
        }

    def decide(self, body: dict[str, Any]) -> None:
        rid = str(body.get("normalized_record_id"))
        if rid not in self.records:
            raise ChoiceRefusedError("UNKNOWN_RECORD", rid)
        decision = make_decision(
            self.working,
            self.records[rid],
            surface_sha256=str(body.get("surface_sha256")),
            decision=str(body.get("decision")),
            reason=str(body.get("reason")),
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

    def bulk(self, body: dict[str, Any]) -> None:
        if self.working["bulk_decisions"]:
            raise ChoiceRefusedError(
                "BULK_DECISION_ALREADY_RECORDED", "undo it first to record another"
            )
        bulk = make_bulk_decision(
            self.working,
            self.records,
            record_ids=list(body.get("normalized_record_ids") or []),
            surface_sha256=dict(body.get("surface_sha256") or {}),
            record_set_digest=str(body.get("record_set_sha256")),
            confirmation=str(body.get("confirmation")),
        )
        self.working["bulk_decisions"] = [bulk]
        self.save()

    def bulk_undo(self, body: dict[str, Any]) -> None:
        self.working["bulk_decisions"] = []
        self.save()


PAGE = """<!doctype html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Egress review</title>
<style nonce="__NONCE__">
:root{--bg:#fafaf7;--fg:#1d1d1b;--muted:#6b6b66;--line:#d9d7cf;--card:#fff;--hit:#ffe08a;--hitline:#b58900;--ok:#1f7a3a;--no:#a62b2b;--accent:#2d4f8a}
@media (prefers-color-scheme:dark){:root{--bg:#161614;--fg:#ecebe6;--muted:#a3a29b;--line:#3a3934;--card:#1f1f1c;--hit:#5c4a0c;--hitline:#e0b73a;--ok:#5fc27d;--no:#e07a7a;--accent:#8fb0e8}}
*{box-sizing:border-box}body{margin:0;background:var(--bg);color:var(--fg);font:15px/1.5 system-ui,sans-serif}
header{position:sticky;top:0;background:var(--bg);border-bottom:1px solid var(--line);padding:10px 16px;display:flex;gap:12px;align-items:center;flex-wrap:wrap;z-index:2}
main{max-width:1100px;margin:0 auto;padding:16px}
button{font:inherit;padding:6px 10px;border:1px solid var(--line);background:var(--card);color:var(--fg);border-radius:6px;cursor:pointer}
button:disabled{opacity:.45;cursor:not-allowed}.approve{border-color:var(--ok);color:var(--ok)}.exclude{border-color:var(--no);color:var(--no)}
.card{background:var(--card);border:1px solid var(--line);border-radius:8px;padding:14px;margin:12px 0}
.muted{color:var(--muted)}.mono{font-family:ui-monospace,Consolas,monospace}
pre.surface{white-space:pre-wrap;word-break:break-word;border:2px solid var(--accent);border-radius:6px;padding:12px;max-height:60vh;overflow:auto;margin:0}
mark{background:var(--hit);color:inherit;outline:1px solid var(--hitline)}
table{border-collapse:collapse;width:100%}td,th{border-bottom:1px solid var(--line);padding:4px 6px;text-align:left;vertical-align:top}
.row{display:flex;gap:8px;flex-wrap:wrap;margin:6px 0}.banner{padding:8px 10px;border-radius:6px;border:1px solid var(--hitline);margin:8px 0}
.error{border-color:var(--no);color:var(--no)}nav a{color:var(--accent);cursor:pointer;margin-right:6px}
</style></head><body>
<header><strong>Egress review, DEVELOPMENT</strong><span id="progress" class="muted"></span>
<button id="prev">&larr; Previous</button><button id="next">Next &rarr;</button><button id="nextOpen">Next undecided</button>
<button id="bulkView">Zero-trigger set</button></header>
<main><div id="error" class="banner error" hidden></div><div id="view"></div>
<p class="muted">Local page on 127.0.0.1. It loads nothing from the internet and sends nothing anywhere but this local server. A trigger is a reason to look, not a finding. Zero triggers does not mean safe. Nothing is decided until you click.</p></main>
<script nonce="__NONCE__">
const TOKEN="__TOKEN__";let S=null,i=0,mode="record";
const $=id=>document.getElementById(id);
function el(tag,attrs,...kids){const e=document.createElement(tag);for(const[k,v]of Object.entries(attrs||{})){if(k==="class")e.className=v;else if(k==="onclick")e.addEventListener("click",v);else e.setAttribute(k,v)}for(const k of kids)e.append(k);return e}
async function load(){const r=await fetch("/api/state",{headers:{"X-Review-Token":TOKEN}});S=await r.json();render()}
async function post(path,body){$("error").hidden=true;const r=await fetch(path,{method:"POST",headers:{"Content-Type":"application/json","X-Review-Token":TOKEN},body:JSON.stringify(body)});const j=await r.json();if(!r.ok){$("error").textContent="Refused: "+j.error;$("error").hidden=false}S=j.state||S;render()}
function render(){$("progress").textContent=(S.total-S.unresolved)+" / "+S.total+" decided, operator "+S.operator_id;mode==="bulk"?renderBulk():renderRecord()}
function renderRecord(){const r=S.records[i],v=$("view");v.replaceChildren();
 const head=el("div",{class:"card"},el("div",{},el("strong",{},r.position+" / "+S.total+"  "),el("span",{class:"mono"},r.normalized_record_id)),
  el("div",{class:"muted mono"},"surface_sha256 "+r.surface_sha256.slice(0,16)+"...  length "+r.surface_length),
  el("div",{},Object.keys(r.trigger_summary).length?"Triggers: "+Object.entries(r.trigger_summary).map(([k,n])=>k+" x"+n).join(", "):"No trigger. This still needs your decision."));
 v.append(head);
 if(r.stale_decision)v.append(el("div",{class:"banner"},"Your earlier decision was bound to a different surface digest and no longer counts. Review again."));
 if(r.decision)v.append(el("div",{class:"banner"},"Decided: "+r.decision.decision+" / "+r.decision.reason+" at "+r.decision.decided_at+" ",el("button",{onclick:()=>post("/api/undo",{normalized_record_id:r.normalized_record_id})},"Undo")));
 if(r.bulk_decision_id)v.append(el("div",{class:"banner"},"Covered by your zero-trigger bulk approval "+r.bulk_decision_id+"."));
 const pre=el("pre",{class:"surface mono"});for(const s of r.segments){pre.append(s.patterns.length?el("mark",{title:s.patterns.join(", ")},s.text):document.createTextNode(s.text))}
 v.append(el("div",{class:"card"},el("div",{},el("strong",{},"Exact surface that would be transmitted"),el("span",{class:"muted"}," (unaltered; highlights are local only)")),pre));
 if(r.triggers.length){const t=el("table",{},el("tr",{},el("th",{},"Pattern"),el("th",{},"Line"),el("th",{},"Matched text in context")));
  for(const x of r.triggers){t.append(el("tr",{},el("td",{class:"mono"},x.pattern),el("td",{},String(x.line)),el("td",{class:"mono"},x.before,el("mark",{},x.text),x.after)))}
  v.append(el("div",{class:"card"},el("strong",{},"Review triggers (hints only)"),t))}
 const secret="secret_like" in r.trigger_summary,zero=!Object.keys(r.trigger_summary).length,locked=!!r.bulk_decision_id;
 const d=(decision,reason)=>post("/api/decide",{normalized_record_id:r.normalized_record_id,surface_sha256:r.surface_sha256,decision,reason});
 const approve=el("div",{class:"row"},el("strong",{},"Approve transmission: "));
 for(const reason of S.approving_reasons){const hide=zero&&reason!=="TRIGGER_REVIEWED_NOT_PERSONAL";if(hide)continue;
  approve.append(el("button",Object.assign({class:"approve",onclick:()=>d("EGRESS_APPROVED",reason)},(secret&&reason!=="TRIGGER_REVIEWED_NOT_PERSONAL")||locked?{disabled:""}:{}),"EGRESS_APPROVED / "+reason))}
 const exclude=el("div",{class:"row"},el("strong",{},"Exclude: "));
 for(const reason of S.excluding_reasons){exclude.append(el("button",Object.assign({class:"exclude",onclick:()=>d("EGRESS_EXCLUDED",reason)},locked?{disabled:""}:{}),"EGRESS_EXCLUDED / "+reason))}
 v.append(el("div",{class:"card"},approve,exclude,secret?el("div",{class:"muted"},"secret_like trigger: only an individual TRIGGER_REVIEWED_NOT_PERSONAL approval can make this record eligible."):""))}
function renderBulk(){const z=S.zero_trigger_set,v=$("view");v.replaceChildren();
 v.append(el("div",{class:"card"},el("strong",{},"Optional: approve the zero-trigger set in bulk"),el("p",{},"These are the undecided records with zero triggers. Zero triggers does not mean safe: approve them only if you reviewed each surface. You can instead decide each one individually.")));
 for(const b of S.bulk_decisions){v.append(el("div",{class:"banner"},"Recorded bulk approval "+b.bulk_decision_id+" of "+b.normalized_record_ids.length+" records at "+b.decided_at+" ",el("button",{onclick:()=>post("/api/bulk-undo",{})},"Undo bulk")))}
 if(!z.normalized_record_ids.length){v.append(el("p",{},"No undecided zero-trigger record."));return}
 const list=el("table",{},el("tr",{},el("th",{},"#"),el("th",{},"Record"),el("th",{},"surface_sha256"),el("th",{},"")));
 for(const rid of z.normalized_record_ids){const r=S.records.find(x=>x.normalized_record_id===rid);list.append(el("tr",{},el("td",{},String(r.position)),el("td",{class:"mono"},rid),el("td",{class:"mono"},z.surface_sha256[rid].slice(0,16)+"..."),el("td",{},el("a",{onclick:()=>{mode="record";i=S.records.indexOf(r);render()}},"open"))))}
 const input=el("input",{type:"text",size:"80","aria-label":"confirmation"});
 v.append(el("div",{class:"card"},list,el("p",{class:"mono"},"record_set_sha256 "+z.record_set_sha256),el("p",{},"To approve exactly these "+z.normalized_record_ids.length+" records, type: ",el("span",{class:"mono"},z.confirmation)),input,
  el("div",{class:"row"},el("button",{class:"approve",onclick:()=>post("/api/bulk",{normalized_record_ids:z.normalized_record_ids,surface_sha256:z.surface_sha256,record_set_sha256:z.record_set_sha256,confirmation:input.value})},"Approve this exact set"))))}
$("prev").addEventListener("click",()=>{mode="record";i=Math.max(0,i-1);render()});
$("next").addEventListener("click",()=>{mode="record";i=Math.min(S.total-1,i+1);render()});
$("nextOpen").addEventListener("click",()=>{mode="record";const n=S.records.findIndex((r,k)=>k>i&&!r.decision&&!r.bulk_decision_id);const f=n>=0?n:S.records.findIndex(r=>!r.decision&&!r.bulk_decision_id);if(f>=0)i=f;render()});
$("bulkView").addEventListener("click",()=>{mode="bulk";render()});
load();
</script></body></html>"""


def make_handler(
    session: ReviewSession, port_holder: dict[str, int]
) -> type[http.server.BaseHTTPRequestHandler]:
    nonce = secrets.token_urlsafe(16)

    class Handler(http.server.BaseHTTPRequestHandler):
        server_version = "egress-review"

        def log_message(self, format: str, *args: Any) -> None:  # noqa: A002 - stdlib signature
            return  # nothing is logged: request bodies name records and choices

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
            # Read the (bounded) body before any answer, refusals included: closing a socket that still
            # holds unread request bytes makes Windows reset the connection, and the client then loses
            # the refusal it was sent.
            length = int(self.headers.get("Content-Length") or 0)
            raw = self.rfile.read(min(length, 1_000_000))
            if not self._host_ok():
                return self._json(421, {"error": "HOST_NOT_LOOPBACK"})
            if self.headers.get("X-Review-Token") != session.token:
                return self._json(403, {"error": "TOKEN_REQUIRED"})
            if self.headers.get("Content-Type") != "application/json":
                return self._json(415, {"error": "JSON_REQUIRED"})
            actions = {
                "/api/decide": session.decide,
                "/api/undo": session.undo,
                "/api/bulk": session.bulk,
                "/api/bulk-undo": session.bulk_undo,
            }
            action = actions.get(self.path)
            if action is None:
                return self._json(404, {"error": "NOT_FOUND"})
            try:
                body = json.loads(raw.decode("utf-8") or "{}")
                action(body if isinstance(body, dict) else {})
            except ChoiceRefusedError as exc:
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
    url = f"http://{LOOPBACK}:{server.server_address[1]}/"
    print(f"Egress review for {session.working['operator_id']}: open {url}")
    print("Every click is saved immediately. Stop with Ctrl+C and run the same command to resume.")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nstopped; decisions so far are saved")
    finally:
        server.server_close()
    return 0


def _validate(
    path: pathlib.Path, *, require_complete: bool
) -> tuple[dict[str, Any], list[tuple[str, str]]]:
    if "holdout" in path.name.lower():
        return {}, [("HOLDOUT_OR_UNKNOWN_SPLIT_REFUSED", path.name)]
    working = json.loads(path.read_text("utf-8"))
    scan, _ = current_scan()
    problems = validate_working_decisions(
        working,
        scan_records=scan["records"],
        committed_doc=json.loads(DECISIONS.read_text("utf-8")),
        holdout_record_ids=holdout_ids(),
        require_complete=require_complete,
    )
    return working, problems


def lint(path: pathlib.Path) -> int:
    working, problems = _validate(path, require_complete=False)
    for code, detail in problems:
        print(f"{code:48} {detail}")
    if problems:
        print(f"FAIL     {len(problems)} problem(s)")
        return 1
    left = len(unresolved_record_ids(working))
    print(
        "ok       the working file is valid"
        + (f"; {left} record(s) still undecided" if left else "; complete")
    )
    return 0


def import_decisions(path: pathlib.Path) -> int:
    working, problems = _validate(path, require_complete=True)
    if problems:
        for code, detail in problems:
            print(f"{code:48} {detail}")
        print("REFUSED  nothing was imported")
        return 1
    committed = committed_decisions(working, json.loads(DECISIONS.read_text("utf-8")))
    DECISIONS.write_bytes(dump(committed))
    print(
        f"imported {len(working['decisions'])} individual and {len(working['bulk_decisions'])} bulk decision(s) into {DECISIONS.name}"
    )
    from build_semantic_egress_eligibility import main as rebuild

    rebuild(["--write"])
    from render_semantic_extraction_packet import main as render

    render(["--write"])
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
    s.add_argument("--port", type=int, default=8765)
    sub.add_parser("lint").add_argument("working")
    sub.add_parser("import").add_argument("working")
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
    return import_decisions(pathlib.Path(args.working))


if __name__ == "__main__":
    sys.exit(main())
