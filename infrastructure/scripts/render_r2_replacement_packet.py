"""Render and validate the GP-R2-Q1 replacement packet and its recipient review.

The Terms-designated address rejected delivery, so a second address was reviewed and
a second packet prepared. Two rules carry this gate:

    A SUPPLIED ADDRESS IS A CLAIM, AND IS ESTABLISHED ON PROVENANCE OR NOT AT ALL.
    AN ESTABLISHED GENERAL CONTACT IS NOT A DESIGNATED CHANNEL.

Mission 1.65 judged a recipient on provenance rather than on spelling, and refused to
infer one from convention. The same standard applies to one handed to this repository:
`d@globalping.io` is accepted because it is read off the provider's own committed
website source as a live mailto link, not because it arrived in an instruction. And it
is recorded as GENERAL CONTACT, because three provider documents designate a different
address for questions about the Terms -- so calling this one designated would assert a
standing it does not have.

`validate()` refuses: a packet whose digest does not recompute; a v2 that reuses v1's
digest; an edited v1; a changed subject or body claimed as preserved; a recipient not
present in a reviewed first-party surface; an address accepted because it was supplied;
a general contact promoted to the designated channel; a review that reads the rendered
page as establishing rather than corroborating; a claim that the designated address is
permanently dead; and any send, approval or connector use.

    uv run python infrastructure/scripts/render_r2_replacement_packet.py
    uv run python infrastructure/scripts/render_r2_replacement_packet.py --check

Deterministic from repository files, so it is safe in CI.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import pathlib

ROOT = pathlib.Path(__file__).resolve().parents[2]
DATA = ROOT / "docs" / "data"

REVIEW = DATA / "globalping-r2-replacement-recipient-review-v1.json"
V2_PACKET = DATA / "globalping-r2-enquiry-packet-v2.json"
V1_PACKET = DATA / "globalping-r2-enquiry-packet-v1.json"
R2_APPROVAL = DATA / "globalping-r2-dispatch-approval-v1.json"

RENDERED = DATA / "mission-1.74.4-r2-replacement-packet-v1.md"

DESIGNATED_CHANNEL_ADDRESS = "legal@globalping.io"
PERMITTED_RELEVANCE = (
    "ESTABLISHED_FIRST_PARTY_GENERAL_CONTACT_NOT_THE_TERMS_DESIGNATED_CHANNEL",
    "ESTABLISHED_FIRST_PARTY_DESIGNATED_CHANNEL",
    "NOT_ESTABLISHED",
)


class ValidationError(RuntimeError):
    """The replacement package says something this gate refuses."""


def _load(path: pathlib.Path) -> dict:
    if not path.exists():
        raise ValidationError(f"{path.name} does not exist")
    record = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(record, dict):
        raise ValidationError(f"{path.name} is not a JSON object")
    return record


def _digest(packet: dict) -> str:
    binding = {key: packet[key] for key in packet["hash_covers"]}
    return hashlib.sha256(
        json.dumps(binding, sort_keys=True, ensure_ascii=False).encode("utf-8")
    ).hexdigest()


def _check_the_review(review: dict) -> None:
    """A supplied address is a claim, and is established on provenance or not at all."""
    if not review["surfaces_reviewed"]:
        raise ValidationError("no surface was reviewed for the recipient")
    if len(review["surfaces_reviewed"]) != review["surfaces_reviewed_count"]:
        raise ValidationError("the surface count does not match the list")

    if review["accepted_because_supplied"]:
        raise ValidationError(
            "the address was accepted because the operator supplied it; a supplied address "
            "is a claim about the world like any other"
        )

    establishment = review["establishment"]
    if establishment["inferred_from_convention"]:
        raise ValidationError("the address was inferred from convention")
    if establishment["single_letter_local_part_treated_as_disqualifying"]:
        raise ValidationError(
            "the address was judged on its spelling; Mission 1.65 judges provenance, "
            "because a string rule refuses a correct address and admits a guessed one"
        )
    if not str(establishment["basis"]).strip():
        raise ValidationError("the establishment states no basis")

    candidate = review["candidate_address"]
    establishing = [
        surface
        for surface in review["surfaces_reviewed"]
        if surface.get("d_address_present") and surface.get("role") != "CORROBORATION_ONLY"
    ]
    if establishment["address_is_established_first_party"] and not establishing:
        raise ValidationError(
            f"{candidate} is called established and appears in no establishing surface"
        )
    if (
        establishing
        and not establishment["read_from_committed_source_rather_than_a_rendered_shell"]
    ):
        raise ValidationError(
            "the address rests on a rendered shell; Mission 1.74 read the provider's "
            "committed source instead, and Mission 1.63 says a summary is not a document"
        )
    for surface in review["surfaces_reviewed"]:
        if (
            surface.get("role") == "CORROBORATION_ONLY"
            and not str(surface.get("why_corroboration_only") or "").strip()
        ):
            raise ValidationError("a corroborating surface does not say why it only corroborates")

    relevance = review["relevance"]
    if relevance["classification"] not in PERMITTED_RELEVANCE:
        raise ValidationError(f"the relevance {relevance['classification']!r} is undefined")
    if relevance["is_it_the_terms_designated_channel"]:
        designating = [
            surface
            for surface in review["surfaces_reviewed"]
            if candidate in surface.get("addresses_found", [])
            and "Terms" in str(surface.get("designates_for", ""))
        ]
        if not designating:
            raise ValidationError(
                "a general contact address was promoted to the Terms-designated channel "
                "with no provider document designating it"
            )
    if relevance["the_terms_designated_channel_remains"] != DESIGNATED_CHANNEL_ADDRESS:
        raise ValidationError("the record moved the Terms-designated channel")
    if not relevance["weaker_than_the_original_basis"]:
        raise ValidationError(
            "a general contact channel is recorded as no weaker than a designation"
        )

    if review["legal_at_globalping_io_status"] != "OPERATOR_ATTESTED_DELIVERY_REJECTED_ONCE":
        raise ValidationError("the designated address's status was overstated")
    if review["not_recorded_as"] != "PERMANENTLY_NONEXISTENT":
        raise ValidationError(
            "one rejected attempt was turned into a permanent fact about an address"
        )
    if not review["what_this_does_not_establish"]:
        raise ValidationError("the review states no limits")
    if not str(review["the_tension_recorded_rather_than_smoothed"]).strip():
        raise ValidationError(
            "the record does not state that the provider designates an address that "
            "rejected mail while publishing another that is live"
        )


def _check_the_packet(v2: dict, v1: dict, review: dict) -> None:
    if _digest(v2) != v2["content_sha256"]:
        raise ValidationError("the replacement packet does not answer to its recorded hash")
    if v2["content_sha256"] == v1["content_sha256"]:
        raise ValidationError(
            "the replacement carries v1's digest; the recipient changed, so the action did"
        )
    for excluded in ("content_sha256", "send_status", "recorded_at"):
        if excluded in v2["hash_covers"]:
            raise ValidationError(f"the packet hashes {excluded}")
    for field in ("recipient", "channel", "subject", "body"):
        if field not in v2["hash_covers"]:
            raise ValidationError(f"{field} is not bound by the packet hash")

    if v2["subject"] != v1["subject"] or v2["body"] != v1["body"]:
        if v2.get("subject_and_body_preserved_exactly"):
            raise ValidationError(
                "the packet claims the approved wording is preserved and it is not"
            )
    elif not v2.get("subject_and_body_preserved_exactly"):
        raise ValidationError("the wording is preserved and the record does not say so")

    if v2["recipient"] != review["candidate_address"]:
        raise ValidationError("the packet's recipient is not the address that was reviewed")
    if not review["establishment"]["address_is_established_first_party"]:
        raise ValidationError("the packet binds a recipient the review did not establish")
    if v2["recipient_guessed"]:
        raise ValidationError("the packet records a guessed recipient")
    if not str(v2["first_party_channel_basis"]).strip():
        raise ValidationError("the packet states no first-party basis for its channel")

    if v2["channel"] == v1["channel"]:
        raise ValidationError(
            "the replacement reuses the designated-channel label for a general contact "
            "address, which asserts a standing it does not have"
        )
    if (
        not v2["channel_differs_from_v1"]
        or not str(v2["why_the_channel_label_changed"] or "").strip()
    ):
        raise ValidationError("the channel changed and the record does not say why")

    if v2["send_status"] != "NOT_AUTHORIZED":
        raise ValidationError("the replacement packet is not marked NOT_AUTHORIZED")
    for flag in ("operator_approval_recorded", "sent", "execution_record_created"):
        if v2[flag]:
            raise ValidationError(f"the replacement packet records {flag}")
    if not v2["prior_approval_does_not_cover_this_packet"]:
        raise ValidationError("the exhausted approval is treated as covering this packet")

    # v1 is superseded, never edited.
    if v2["supersedes"] != V1_PACKET.name:
        raise ValidationError("the replacement does not name what it supersedes")
    if _digest(v1) != v1["content_sha256"]:
        raise ValidationError("version 1 no longer answers to its own hash; it was edited")
    if v1["send_status"] != "NOT_AUTHORIZED" or v1["sent"]:
        raise ValidationError("version 1 was edited")


def _check_the_exhausted_approval(approval: dict, v2: dict) -> None:
    execution = approval["execution"]
    if execution["status"] != "DISPATCH_ATTEMPTED_DELIVERY_FAILED":
        raise ValidationError(
            "a replacement packet exists while the earlier dispatch does not record a "
            "failure; a replacement without a failed attempt is a second first attempt"
        )
    if not execution.get("approval_exhausted"):
        raise ValidationError("the earlier approval is not recorded as exhausted")
    if execution.get("provider_contacted"):
        raise ValidationError("the bounced attempt is recorded as a provider contact")
    if approval["approved_action"]["approved_content_sha256"] == v2["content_sha256"]:
        raise ValidationError(
            "the exhausted approval names the replacement packet's digest, so it would "
            "authorise a send it never approved"
        )
    if approval["approved_action"]["recipient"] == v2["recipient"]:
        raise ValidationError("the exhausted approval already names this recipient")


def validate() -> tuple[dict, dict, dict]:
    review = _load(REVIEW)
    v2 = _load(V2_PACKET)
    v1 = _load(V1_PACKET)
    approval = _load(R2_APPROVAL)
    try:
        _check_the_review(review)
        _check_the_packet(v2, v1, review)
        _check_the_exhausted_approval(approval, v2)
    except (KeyError, TypeError) as error:
        raise ValidationError(f"the record does not carry {error!r}") from error
    return review, v2, v1


def render(review: dict, v2: dict, v1: dict) -> str:
    relevance = review["relevance"]
    lines = [
        "# Mission 1.74.4 — The designated address bounced, and a replacement is prepared",
        "",
        "Generated from `globalping-r2-replacement-recipient-review-v1.json` and "
        "`globalping-r2-enquiry-packet-v2.json`. Do not edit by hand.",
        "",
        "## What the provider's own documents say",
        "",
        "| surface | addresses | designates for |",
        "|---|---|---|",
    ]
    for surface in review["surfaces_reviewed"]:
        addresses = ", ".join(f"`{a}`" for a in surface["addresses_found"])
        lines.append(f"| {surface['surface']} | {addresses} | {surface['designates_for']} |")
    lines += [
        "",
        review["the_tension_recorded_rather_than_smoothed"],
        "",
        "## The address is established, and it is not a designation",
        "",
        f"- established first-party: **{review['establishment']['address_is_established_first_party']}**",
        f"- read from committed source rather than a rendered shell: "
        f"**{review['establishment']['read_from_committed_source_rather_than_a_rendered_shell']}**",
        f"- accepted because it was supplied: **{review['accepted_because_supplied']}**",
        f"- is it the Terms-designated channel: "
        f"**{relevance['is_it_the_terms_designated_channel']}**",
        f"- the Terms-designated channel remains: "
        f"`{relevance['the_terms_designated_channel_remains']}`",
        "",
        f"**`{relevance['classification']}`**",
        "",
        relevance["why_it_is_still_the_relevant_remaining_route"],
        "",
        review["establishment"]["why_not"],
        "",
        "## What this does not establish",
        "",
    ]
    for item in review["what_this_does_not_establish"]:
        lines.append(f"- {item}")
    lines += [
        "",
        f"The designated address is recorded as `{review['legal_at_globalping_io_status']}` "
        f"and explicitly not as `{review['not_recorded_as']}`. {review['why']}",
        "",
        "## The replacement packet",
        "",
        "| | v1 | v2 |",
        "|---|---|---|",
        f"| recipient | `{v1['recipient']}` | `{v2['recipient']}` |",
        f"| channel | `{v1['channel']}` | `{v2['channel']}` |",
        # Derived rather than asserted: the page must not be able to say "identical"
        # about wording that is not.
        f"| subject | {'identical' if v2['subject'] == v1['subject'] else 'CHANGED'} "
        f"| {'identical' if v2['subject'] == v1['subject'] else 'CHANGED'} |",
        f"| body | {'identical' if v2['body'] == v1['body'] else 'CHANGED'} "
        f"| {'identical' if v2['body'] == v1['body'] else 'CHANGED'} |",
        f"| digest | `{v1['content_sha256'][:16]}…` | `{v2['content_sha256'][:16]}…` |",
        f"| send status | `{v1['send_status']}` | `{v2['send_status']}` |",
        "",
        v2["why_no_explanatory_sentence_was_added"],
        "",
        v2["why_the_channel_label_changed"],
        "",
        "## The earlier approval is spent",
        "",
        v2["why"],
        "",
        "**No approval covers this packet.** A new recipient is a new action and needs a "
        "new explicit operator approval.",
        "",
    ]
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()

    try:
        review, v2, v1 = validate()
    except ValidationError as error:
        print(f"REFUSED  R2 replacement packet: {error}")
        return 1

    text = render(review, v2, v1)
    if args.check:
        if not RENDERED.exists():
            print(f"DRIFT    {RENDERED.name} does not exist")
            return 1
        if RENDERED.read_text(encoding="utf-8") != text:
            print(f"DRIFT    {RENDERED.name} does not match its records")
            return 1
        print("ok       the R2 replacement package matches its records")
        return 0

    RENDERED.write_text(text, encoding="utf-8", newline="\n")
    print(f"wrote    {RENDERED.name} ({len(text.splitlines())} lines)")
    print(f"recipient {v2['recipient']}")
    print(f"relevance {review['relevance']['classification']}")
    print(f"status    {v2['send_status']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
