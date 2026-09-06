"""Render and validate the GP-R1-Q1 dispatch approval.

One approval, recorded beside the document it approves rather than inside it, and

    AN APPROVAL IS NOT AN EXECUTION.

That distinction is the whole of this gate, and it is unusually easy to lose here:
once the approval exists, **every field an execution record needs is already known**
-- mechanism, target, identity, title and body are all pinned -- so a record could
fill itself in completely and be entirely fictional. `SENT` is therefore reachable
only through an explicit operator attestation plus an issue URL that no frozen
document contains.

`validate()` refuses: an approval that no longer names the packet as stored; an
approval written into the packet it approves; a packet whose own fields were
edited to say it was approved or sent; an approval whose digest does not recompute
over its binding fields, or which hashes its own digest, its execution status or
its date; an execution claiming a post with no attestation and no URL;
`BYTE_VERIFIED` with nothing to verify against; more posts than the approval
authorises; a second enquiry carried along by an approval that named one; and any
issue this repository created itself.

    uv run python infrastructure/scripts/render_r1_dispatch_approval.py
    uv run python infrastructure/scripts/render_r1_dispatch_approval.py --check

Deterministic from repository files, so it is safe in CI.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import pathlib
import re

ROOT = pathlib.Path(__file__).resolve().parents[2]
DATA = ROOT / "docs" / "data"

APPROVAL = DATA / "globalping-r1-dispatch-approval-v1.json"
R1_PACKET = DATA / "globalping-r1-enquiry-packet-v1.json"
R2_PACKET = DATA / "globalping-r2-enquiry-packet-v1.json"
CLOSURE = DATA / "globalping-residual-closure-v1.json"

RENDERED = DATA / "mission-1.74.1-r1-dispatch-approval-v1.md"

EXECUTION_STATUSES = ("PENDING_MANUAL_OPERATOR_ACTION", "SENT", "SUPERSEDED", "WITHDRAWN")
ATTESTATION_LEVELS = ("OPERATOR_ATTESTED", "BYTE_VERIFIED")

HARD_ZERO = (
    "PUBLIC_POSTS",
    "GITHUB_ISSUES_CREATED",
    "GH_INVOCATIONS",
    "EMAILS_SENT",
    "MAILBOX_SEARCHES",
    "PROVIDER_CONTACTS",
    "ENQUIRIES_SENT",
    "GLOBALPING_API_EXECUTIONS",
    "GLOBALPING_MEASUREMENTS_CREATED",
    "TARGET_HTTP_REQUESTS",
    "SROS_FETCHER_RUNS",
    "ACCOUNTS_CREATED",
    "TOKENS_CREATED",
    "CREDENTIAL_READS",
    "FIRST_PARTY_DOCUMENT_REQUESTS",
    "SOURCES_REGISTERED",
    "SOURCE_GOVERNANCE_MUTATIONS",
    "CLAIMS_CREATED",
    "EVIDENCE_CREATED",
    "INDEPENDENCE_GROUPS_CREATED",
    "RELIABILITY_VALUES_ASSIGNED",
    "SCORES",
    "OPPORTUNITY_MUTATIONS",
    "MODEL_CALLS",
    "EMBEDDINGS",
    "MIGRATIONS",
    "CONSTRUCTS_SELECTED",
    "QUANTITY_CLASSES_SELECTED",
    "CANONICAL_MUTATIONS",
)


class ValidationError(RuntimeError):
    """The approval record says something this gate refuses."""


def _load(path: pathlib.Path) -> dict:
    if not path.exists():
        raise ValidationError(f"{path.name} does not exist")
    record = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(record, dict):
        raise ValidationError(f"{path.name} is not a JSON object")
    return record


def _packet_digest(packet: dict) -> str:
    binding = {key: packet[key] for key in packet["hash_covers"]}
    return hashlib.sha256(
        json.dumps(binding, sort_keys=True, ensure_ascii=False).encode("utf-8")
    ).hexdigest()


def _check_the_approval_still_names_the_packet(approval: dict, packet: dict) -> None:
    """The approval names a document by its hash, and the hash is recomputed."""
    block = approval["approval"]
    recomputed = _packet_digest(packet)
    if recomputed != packet["content_sha256"]:
        raise ValidationError("the packet no longer answers to its own recorded hash")
    if approval["approved_action"]["approved_content_sha256"] != recomputed:
        raise ValidationError(
            "the approval names a hash the packet does not have, so it approves a document "
            "that is not this one"
        )
    if not block["hash_recomputed_from_the_packet_as_stored"]:
        raise ValidationError("the approval asserts a hash rather than recomputing it")

    on_disk = hashlib.sha256(R1_PACKET.read_bytes()).hexdigest()
    if block["packet_file_sha256"] != on_disk:
        raise ValidationError("the packet file changed after the approval was recorded")
    if block["packet_edited_by_this_mission"] or block["packet_content_sha256_changed"]:
        raise ValidationError("the approval records an edit to the document it approves")

    body_digest = hashlib.sha256(packet["body"].encode("utf-8")).hexdigest()
    if block["approved_body_sha256"] != body_digest:
        raise ValidationError("the approved body digest does not match the packet body")


def _check_the_approval_stayed_out_of_the_packet(packet: dict) -> None:
    """Mission 1.66. The approval must not have leaked into the document it names."""
    if packet["operator_approval_recorded"]:
        raise ValidationError(
            "the packet now records an approval; the approval belongs beside it, not inside it"
        )
    if packet["sent"] or packet["execution_record_created"]:
        raise ValidationError("the packet was edited to claim it was sent")
    if packet["send_status"] != "NOT_AUTHORIZED":
        raise ValidationError(
            "the packet's own send status was edited; it means THIS DOCUMENT RECORDS NO "
            "AUTHORIZATION and is not where an approval is recorded"
        )


def _check_the_action_is_bound(approval: dict, packet: dict) -> None:
    """Mission 1.65's envelope rule: the digest binds the ACTION, not the document."""
    action = approval["approved_action"]
    binding = {key: action[key] for key in action["hash_covers"]}
    digest = hashlib.sha256(
        json.dumps(binding, sort_keys=True, ensure_ascii=False).encode("utf-8")
    ).hexdigest()
    if digest != action["approval_sha256"]:
        raise ValidationError("the approved action does not answer to its recorded hash")

    for excluded in ("approval_sha256", "execution", "recorded_at"):
        if excluded in action["hash_covers"]:
            raise ValidationError(f"the approval hashes {excluded}")
        if excluded not in action["hash_excludes"]:
            raise ValidationError(f"the approval does not declare {excluded} excluded")

    for field in ("mechanism", "target_repository", "identity", "approved_title"):
        if not str(action[field]).strip():
            raise ValidationError(f"the approved action has no {field}")
        if field not in action["hash_covers"]:
            raise ValidationError(f"{field} is not bound by the approval hash")

    if action["approved_title"] != packet["subject"]:
        raise ValidationError("the approved title is not the packet's subject")
    if action["approves"] != packet["question_id"]:
        raise ValidationError("the approval names a different enquiry than the packet it cites")
    if not action["channel_matches_the_packet"]:
        raise ValidationError("the approved mechanism does not match the packet's channel")
    if action["maximum_public_posts"] != 1:
        raise ValidationError("one approval authorises exactly one public post")


def _check_execution(approval: dict) -> None:
    """An approval says an action MAY be performed. Only a performance says it WAS."""
    execution = approval["execution"]
    if execution["status"] not in EXECUTION_STATUSES:
        raise ValidationError(f"the execution status {execution['status']!r} is undefined")

    posts = execution["public_posts_made"]
    if posts > approval["approved_action"]["maximum_public_posts"]:
        raise ValidationError(
            f"{posts} public posts were made and the approval authorises "
            f"{approval['approved_action']['maximum_public_posts']}"
        )

    if execution["issue_created_by_this_repository"]:
        raise ValidationError("this repository created the issue, and it may not")
    if execution["gh_issue_create_invoked"]:
        raise ValidationError("gh issue create was invoked, and it may not be")

    # Mission 1.74.7. This counter used to refuse EVERY GitHub API call, while Mission
    # 1.74.1 defined the upgrade to BYTE_VERIFIED as a raw read of the issue body -- so
    # the gate demanded a comparison and forbade the only mechanism that makes one. What
    # the rule protects is that this repository never WROTE, and a read is not that.
    if execution["github_api_write_calls_made_by_this_repository"] != 0:
        raise ValidationError("this repository wrote to GitHub on the operator's behalf")
    reads = execution["github_api_read_calls_made_by_this_issue_record"]
    if not isinstance(reads, int) or reads < 0:
        raise ValidationError("the record does not state how many raw reads it made")
    if len(execution["github_api_read_endpoints"]) != reads:
        raise ValidationError("the listed read endpoints do not match the recorded count")
    for endpoint in execution["github_api_read_endpoints"]:
        if not endpoint.startswith("GET "):
            raise ValidationError(f"the endpoint {endpoint!r} is not a read")

    level = execution["attestation_level"]
    if level is not None and level not in ATTESTATION_LEVELS:
        raise ValidationError(f"the attestation level {level!r} is undefined")

    if execution["status"] == "PENDING_MANUAL_OPERATOR_ACTION":
        if posts != 0:
            raise ValidationError("the execution is pending and records a post")
        if execution["issue_url"] is not None:
            raise ValidationError("the execution is pending and records an issue URL")
        if execution["operator_attestation_recorded"] or level is not None:
            raise ValidationError("the execution is pending and records an attestation")

    if execution["status"] == "SENT":
        if not execution["operator_attestation_recorded"]:
            raise ValidationError(
                "SENT with no operator attestation; this repository cannot observe the post"
            )
        if posts < 1:
            raise ValidationError("SENT with no post recorded")
        if level is None:
            raise ValidationError("SENT with no attestation level")
        if not str(execution.get("attested_by") or "").strip():
            raise ValidationError("SENT with nobody named as the attester")

        # This channel produces a durable public artifact, so a send that cannot name one
        # is a send nothing can ever be checked against.
        url = str(execution["issue_url"] or "").strip()
        if not url:
            raise ValidationError("SENT with no issue URL on a channel that produces one")
        match = re.fullmatch(r"https://github\.com/([^/]+/[^/]+)/issues/(\d+)", url)
        if not match:
            raise ValidationError(f"the issue URL {url!r} is not a GitHub issue URL")
        if match.group(1) != approval["approved_action"]["target_repository"]:
            raise ValidationError("the issue URL names a repository the approval did not")
        if execution.get("issue_number") != int(match.group(2)):
            raise ValidationError("the recorded issue number disagrees with its own URL")

        # Mission 1.63. A retrieval summary is not a document, so the higher level
        # requires a raw comparison rather than a corroborating fetch -- and every SENT
        # record must SAY whether one happened, rather than leaving a later reader unable
        # to tell an unverified send from an unrecorded verification.
        if not isinstance(execution.get("raw_body_compared"), bool):
            raise ValidationError("a SENT record does not state whether the body was compared raw")
        if level == "BYTE_VERIFIED" and not execution.get("raw_body_compared"):
            raise ValidationError(
                "BYTE_VERIFIED without a raw body comparison; a summarising retrieval "
                "corroborates an attestation and does not replace it"
            )
        # A comparison needs something to compare against, and the only route to the
        # stored body is a read. A record claiming one with no read compared nothing.
        if execution["raw_body_compared"] and reads < 1:
            raise ValidationError("the body is recorded as compared raw and nothing was read")
        if level == "BYTE_VERIFIED":
            _check_byte_verification(approval, execution)
        if (
            level == "OPERATOR_ATTESTED"
            and not str(execution.get("byte_verification_not_reached_because") or "").strip()
        ):
            raise ValidationError(
                "OPERATOR_ATTESTED on a channel that can reach higher, with no reason given"
            )

    if not execution["byte_verification_is_possible_for_this_channel"]:
        raise ValidationError(
            "the record denies that a public issue can be byte-verified, which is what "
            "distinguishes this channel from a manual mail send"
        )
    for field in ("upgrade_path", "reachable_only_through"):
        if not str(execution[field]).strip():
            raise ValidationError(f"the execution states no {field}")


def _check_byte_verification(approval: dict, execution: dict) -> None:
    """Mission 1.74.7. BYTE_VERIFIED is a comparison, so the record must show one.

    The danger here is the same as everywhere in this arc: every number the block needs
    is already in the record, so a fabricated block would look exactly like a real one.
    What makes it checkable is that the digests must AGREE with the approval's own
    `approved_body_sha256`, which was recorded before anything was posted.
    """
    block = execution["byte_verification"]

    if block["went_through_a_summarising_extraction"]:
        raise ValidationError(
            "the byte verification went through a summarising extraction; Mission 1.63 "
            "settled that a summary cannot establish byte equality"
        )
    if block["retrieval_method"] != "RAW_GITHUB_REST_API_READ":
        raise ValidationError(
            f"the retrieval method {block['retrieval_method']!r} does not return stored bytes"
        )
    if not str(block["endpoint"]).startswith("GET "):
        raise ValidationError("the byte verification names no read endpoint")
    if str(execution["issue_url"]).rsplit("/", 1)[-1] not in block["endpoint"]:
        raise ValidationError("the endpoint read is not the issue the record attests to")

    approved = approval["approval"]["approved_body_sha256"]
    for field in ("posted_body_sha256", "frozen_packet_body_sha256", "approved_body_sha256"):
        if block[field] != approved:
            raise ValidationError(
                f"{field} disagrees with the body digest the approval recorded before the post"
            )
    for flag in (
        "posted_body_is_byte_identical_to_the_frozen_body",
        "posted_title_is_byte_identical_to_the_approved_title",
    ):
        if not block[flag]:
            raise ValidationError(f"BYTE_VERIFIED while {flag} is false")

    if block["raw_api_reads_of_this_issue"] < 1:
        raise ValidationError("the byte verification records no read of the issue")
    if not str(block["what_this_does_not_establish"]).strip():
        raise ValidationError("the byte verification states no limit")
    if not str(block["performed_by_mission"]).strip():
        raise ValidationError("the byte verification names no mission that performed it")


def _check_integrity_rules(approval: dict) -> None:
    checks = approval["integrity_checks_frozen_before_any_post"]
    for flag in (
        "posted_title_must_match_approved_title",
        "posted_body_must_match_the_frozen_packet_body",
        "posted_repository_must_match_target",
        "one_approval_authorises_exactly_one_public_post",
        "a_second_post_is_reported_as_a_duplicate_not_silently_accepted",
        "a_divergence_never_repairs_this_approval",
        "a_divergence_is_recorded_beside_it",
    ):
        if checks[flag] is not True:
            raise ValidationError(f"the integrity rule {flag} was weakened")


def _check_scope(approval: dict) -> None:
    """The operator approved one enquiry, and one is what may travel."""
    scope = approval["scope"]
    if scope["approved_enquiries"] != ["GP-R1-Q1"]:
        raise ValidationError("the approved set is not exactly GP-R1-Q1")
    if scope["r2_approved"] or scope["r2_packet_edited"]:
        raise ValidationError("R2 was carried along by an approval that named R1")

    r2 = _load(R2_PACKET)
    if r2["send_status"] != scope["r2_send_status_unchanged"]:
        raise ValidationError("the R2 packet's send status moved")
    if r2["send_status"] != "NOT_AUTHORIZED":
        raise ValidationError("the R2 packet is no longer unauthorised")
    if r2["operator_approval_recorded"] or r2["sent"]:
        raise ValidationError("the R2 packet records an approval or a send")

    if scope["residuals_closed_by_this_mission"] != 0:
        raise ValidationError("an approval to ask closed a residual")
    if not scope["an_approval_to_ask_is_not_an_answer"]:
        raise ValidationError("the record treats an approval to ask as an answer")
    if scope["qualification_recomputed"]:
        raise ValidationError("the qualification was recomputed by an approval mission")

    closure = _load(CLOSURE)
    if closure["enquiries"]["enquiries_sent"] != 0:
        raise ValidationError("Mission 1.74's closure record now reports a send")
    if closure["residuals_remaining"] != 2:
        raise ValidationError("Mission 1.74's residual count was edited")


def _check_accounting(approval: dict) -> None:
    accounting = approval["mission_accounting"]
    for counter in HARD_ZERO:
        if counter not in accounting:
            raise ValidationError(f"the accounting does not report {counter}")
        if accounting[counter] != 0:
            raise ValidationError(f"{counter} is {accounting[counter]}, and it must be 0")

    parallel = approval["parallel_state_untouched"]
    if parallel["onyphe_response_status"] != "NOT_CHECKED_AFTER_DISPATCH":
        raise ValidationError("the ONYPHE response status moved")
    if parallel["netlas_contact_state"] != "STILL_PENDING":
        raise ValidationError("the Netlas contact state moved")
    for flag in (
        "onyphe_mailbox_searched",
        "netlas_enquiry_sent",
        "scanner_arc_reopened",
        "adr_039_weakened",
        "mission_1_74_records_edited",
    ):
        if parallel[flag] is not False:
            raise ValidationError(f"{flag} is true, and this mission may not do it")

    action = approval["recommended_next_action"]
    if action["performed_by"] != "OPERATOR":
        raise ValidationError("the next action is not assigned to the operator")
    if not action["this_repository_may_not_perform_it"]:
        raise ValidationError("the record permits this repository to perform the post")
    if not action["r2_dispatch_requires_its_own_approval"]:
        raise ValidationError("R2 dispatch is treated as already approved")


def validate() -> dict:
    approval = _load(APPROVAL)
    packet = _load(R1_PACKET)

    if not approval["approval"]["approval_given"]:
        raise ValidationError("this record exists to carry an approval and carries none")
    if not str(approval["approval"]["approved_by"]).strip():
        raise ValidationError("the approval names no approver")

    # A field this gate reads and the record omits is a refusal, never a crash: a
    # truncated record must not be able to skip a check by not carrying its subject.
    try:
        _check_the_approval_still_names_the_packet(approval, packet)
        _check_the_approval_stayed_out_of_the_packet(packet)
        _check_the_action_is_bound(approval, packet)
        _check_execution(approval)
        _check_integrity_rules(approval)
        _check_scope(approval)
        _check_accounting(approval)
    except (KeyError, TypeError) as error:
        raise ValidationError(f"the record does not carry {error!r}") from error
    return approval


def render(approval: dict) -> str:
    packet = _load(R1_PACKET)
    action = approval["approved_action"]
    execution = approval["execution"]

    lines = [
        "# Mission 1.74.1 — One enquiry approved, and nothing posted",
        "",
        "Generated from `globalping-r1-dispatch-approval-v1.json`. Do not edit by hand.",
        "",
        f"**Execution status: `{execution['status']}`**",
        "",
        "## What was approved",
        "",
        "| | |",
        "|---|---|",
        f"| enquiry | `{action['approves']}` |",
        f"| mechanism | `{action['mechanism']}` |",
        f"| target | `{action['target_repository']}` |",
        f"| identity | `{action['identity']}` |",
        f"| title | {action['approved_title']} |",
        f"| maximum public posts | **{action['maximum_public_posts']}** |",
        f"| approved content hash | `{action['approved_content_sha256'][:16]}…` |",
        f"| approval hash | `{action['approval_sha256'][:16]}…` |",
        "",
        "The approval hash binds "
        + ", ".join(f"`{f}`" for f in action["hash_covers"])
        + ", and excludes "
        + ", ".join(f"`{f}`" for f in action["hash_excludes"])
        + ".",
        "",
        action["why_that_differs_from_mission_1_66"],
        "",
        "## The approval is not in the document it approves",
        "",
        approval["approval"]["why"],
        "",
        f"The packet still reads `send_status: {packet['send_status']}`, "
        f"`operator_approval_recorded: {packet['operator_approval_recorded']}`, "
        f"`sent: {packet['sent']}` — unchanged, and its file hash is recorded here so an "
        "edit is detectable.",
        "",
        "## An approval is not an execution",
        "",
        "| | |",
        "|---|---|",
        f"| public posts made | {execution['public_posts_made']} |",
        f"| issue URL | {execution['issue_url']} |",
        f"| issue created by this repository | {execution['issue_created_by_this_repository']} |",
        f"| `gh issue create` invoked | {execution['gh_issue_create_invoked']} |",
        f"| GitHub API **write** calls by this repository | "
        f"{execution['github_api_write_calls_made_by_this_repository']} |",
        f"| GitHub API **read** calls against this issue | "
        f"{execution['github_api_read_calls_made_by_this_issue_record']} |",
        f"| operator attestation recorded | {execution['operator_attestation_recorded']} |",
        f"| attestation level | {execution['attestation_level']} |",
        "",
        execution["why_byte_verification_is_possible_here"],
        "",
        execution["why_the_counter_was_split"],
        "",
        f"**Upgrade path.** {execution['upgrade_path']}",
        "",
        "## What this approval does not cover",
        "",
        f"- **R2 is not approved.** {approval['scope']['why_r2_is_not_covered']}.",
        f"- Its packet still reads `{approval['scope']['r2_send_status_unchanged']}`.",
        f"- Residuals closed by this mission: "
        f"**{approval['scope']['residuals_closed_by_this_mission']}**. "
        "An approval to ask is not an answer.",
        "",
        "## Nothing moved",
        "",
        "| | |",
        "|---|---|",
    ]
    for counter in (
        "PUBLIC_POSTS",
        "GITHUB_ISSUES_CREATED",
        "GH_INVOCATIONS",
        "EMAILS_SENT",
        "PROVIDER_CONTACTS",
        "ENQUIRIES_SENT",
        "MAILBOX_SEARCHES",
        "GLOBALPING_API_EXECUTIONS",
        "CANONICAL_MUTATIONS",
        "MODEL_CALLS",
    ):
        lines.append(f"| {counter} | {approval['mission_accounting'][counter]} |")
    lines += [
        "",
        f"**Next: {approval['recommended_next_action']['action']}.** "
        f"Performed by {approval['recommended_next_action']['performed_by']}; "
        "this repository may not perform it.",
        "",
    ]
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()

    try:
        approval = validate()
    except ValidationError as error:
        print(f"REFUSED  R1 dispatch approval: {error}")
        return 1

    text = render(approval)
    if args.check:
        if not RENDERED.exists():
            print(f"DRIFT    {RENDERED.name} does not exist")
            return 1
        if RENDERED.read_text(encoding="utf-8") != text:
            print(f"DRIFT    {RENDERED.name} does not match its record")
            return 1
        print("ok       the R1 dispatch approval matches its record")
        return 0

    RENDERED.write_text(text, encoding="utf-8", newline="\n")
    print(f"wrote    {RENDERED.name} ({len(text.splitlines())} lines)")
    print(f"approval {approval['approved_action']['approval_sha256'][:16]}…")
    print(f"status   {approval['execution']['status']}")
    print(f"posts    {approval['execution']['public_posts_made']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
