"""Record ONE reliability assessment that a person has decided.

`evidence-reliability-review-guide-v1.md` is how a reviewer reaches a judgement.
This is how they write it down, and it is deliberately not more than that.

**What this tool does not do, and cannot be made to do.** It does not choose a
value, suggest one, default one, or derive one from anything the system already
knows. `resolve_reliability` is the read path and takes no opinion; this is the
write path and holds none. Every judgement field is required, non-blank, and
supplied by the operator in a review file they wrote.

**Why a review FILE rather than command-line flags.** An assessment carries a
rationale, a stated limitation and at least one document-backed basis row. Those
are paragraphs, not flags, and a reviewer who has to fit a limitation into a
shell argument will write a shorter one than they mean. The file is also the
artefact they can re-read before confirming, which is the point of §8 of the
mission brief and of the guide's "write down the failure mode first".

**The packet is facts; the file is judgement.** `--packet <scope>` prints what
the repository has already established about a scope -- retrieved documents and
their findings -- and emits a template whose factual basis rows are filled in
and whose judgement fields are **empty**. Pre-filling a limitation and recording
it as though a person wrote it is the one thing that would make this tool a
forgery, and blank fields are refused rather than defaulted.

**`reviewed_by` names a person.** Not a team, not a script, not a model. The
guide says so and the contract enforces non-blank; this tool additionally
refuses a small set of impersonal identifiers, because "operator" is what gets
typed when nobody wants to be the reviewer.

Usage:

    python infrastructure/scripts/record_reliability_assessment.py --packet ted-eu-procurement-contrast
    python infrastructure/scripts/record_reliability_assessment.py --review-file my-review.json
    python infrastructure/scripts/record_reliability_assessment.py --review-file my-review.json --apply

Related: `evidence-reliability-contract-v1.md` (what a value means), ADR-026
(scope and binding), `ted-eu-evidence-reliability-v1.md` (the documentary review
this exists to let a person conclude).
"""

from __future__ import annotations

import argparse
import json
import os
import pathlib
import sys
import uuid
from datetime import UTC, datetime
from typing import Any

sys.path.insert(0, "packages/evidence-reliability/python")
sys.path.insert(0, "packages/contracts/python")

from sros_contracts import (  # noqa: E402
    ClaimType,
    ReliabilityAssessmentOrigin,
    ReliabilityBasisType,
)
from sros_evidence_reliability import (  # noqa: E402
    ReliabilityAssessment,
    ReliabilityBasis,
    ReliabilityScope,
)

RECORD_KIND_REGISTRY = "normalization_record_kind"
CONFIRMATION = "record it"

# Identifiers that name nobody. `reviewed_by` is the field a later reader uses
# to ask "who decided this and on what basis"; a value from this list answers
# neither half. Refused rather than warned about, because a warning is what a
# reviewer in a hurry scrolls past.
IMPERSONAL = frozenset(
    {"operator", "admin", "system", "root", "user", "claude", "ai", "assistant", "bot", "script"}
)

# Judgement fields. Every one is supplied by the person and none has a default,
# a suggestion or a fallback anywhere in this file.
JUDGEMENT_FIELDS = ("reliability", "reviewed_by", "rationale", "stated_limitation")


# --------------------------------------------------------------- review packets
#
# A packet is a FACT SHEET for one scope: what the repository has already
# established, with its documents. It contains no proposed value and no proposed
# limitation, and adding either here would defeat the tool.

PACKETS: dict[str, dict[str, Any]] = {
    "ted-eu-procurement-contrast": {
        "scope": {
            "source_id": "ted-eu",
            "resource_id": "notices/eforms-contract-and-award",
            "record_kind_id": "procurement_notice",
            "claim_type": "OBSERVED",
            "proposition_kind": "source_reported_procurement_value_contrast",
        },
        "review_document": "docs/data/ted-eu-evidence-reliability-v1.md",
        "what_the_evidence_supports": (
            "That TED published a structured value the buyer submitted. NOT that the "
            "amount is an accurate account of the procurement: no first-party source "
            "establishes that TED verifies it."
        ),
        "material_findings": [
            "BT-161 is defined as 'The value of all contracts awarded in this notice, "
            "including options and renewals' -- so the figure is not what was paid, and "
            "options may never be exercised.",
            "The value is supplied by the contracting authority. TED validates "
            "conformance: 60 published rules name BT-161 and every one is a presence, "
            "absence or notice-type constraint. None concerns the amount's correctness.",
            "BT-161 may be LAWFULLY WITHHELD from immediate publication (BT-195 to "
            "BT-198), so a cohort built from published values covers the published "
            "subset and the missingness is not random.",
            "The statistic is a maximum minus a minimum, which is the statistic most "
            "exposed to a missing extreme.",
        ],
        # FACTS, with their documents. Pre-filled because they are retrieved
        # documents rather than judgements -- the reviewer checks them, and may
        # edit or remove any they do not accept.
        "basis": [
            {
                "basis_type": "SOURCE_DOCUMENTATION",
                "document_title": "eForms SDK 1.15.1 field repository (fields.json)",
                "document_url": "https://github.com/OP-TED/eForms-SDK/blob/1.15.1/fields/fields.json",
                "section_reference": "BT-161-NoticeResult",
                "summarized_finding": (
                    "TOTAL_VALUE is BT-161, notice level, non-repeatable, at XPath "
                    "efac:NoticeResult/cbc:TotalAmount, with a companion currency field."
                ),
                "retrieved_at": "2026-09-01T00:00:00+00:00",
            },
            {
                "basis_type": "MEASUREMENT_METHODOLOGY",
                "document_title": "eForms SDK 1.15.1 business-term definitions (business-term_en.xml)",
                "document_url": "https://github.com/OP-TED/eForms-SDK/blob/1.15.1/translations/business-term_en.xml",
                "section_reference": "business-term|description|BT-161",
                "summarized_finding": (
                    "BT-161 is 'The value of all contracts awarded in this notice, "
                    "including options and renewals'."
                ),
                "retrieved_at": "2026-09-01T00:00:00+00:00",
            },
            {
                "basis_type": "KNOWN_LIMITATION",
                "document_title": "eForms SDK 1.15.1 business-term definitions, BT-195 to BT-198",
                "document_url": "https://github.com/OP-TED/eForms-SDK/blob/1.15.1/translations/business-term_en.xml",
                "section_reference": "business-term|description|BT-195",
                "summarized_finding": (
                    "Result values, of which BT-161 is one, may be withheld from "
                    "immediate publication with a justification and a later date."
                ),
                "retrieved_at": "2026-09-01T00:00:00+00:00",
            },
            {
                "basis_type": "KNOWN_LIMITATION",
                "document_title": "eForms SDK 1.15.1 business rules (rule_en.xml)",
                "document_url": "https://github.com/OP-TED/eForms-SDK/blob/1.15.1/translations/rule_en.xml",
                "section_reference": "BR-BT-00161-*",
                "summarized_finding": (
                    "60 published rules govern where BT-161 may appear. All are presence, "
                    "absence or notice-type constraints; none concerns the amount's "
                    "correctness."
                ),
                "retrieved_at": "2026-09-01T00:00:00+00:00",
            },
        ],
    }
}


def _fail(message: str) -> int:
    print(f"REFUSED: {message}", file=sys.stderr)
    return 2


def _template(packet: dict[str, Any]) -> dict[str, Any]:
    """A review file with the FACTS filled in and every judgement blank."""
    return {
        "_instructions": [
            "Fill in reliability, reviewed_by, rationale and stated_limitation.",
            "Every one is refused if blank. Nothing here proposes a value.",
            "reviewed_by names a PERSON. Not a team, not a script, not a model.",
            "Check each basis row against its document and edit or remove any you "
            "do not accept. At least one document-backed row is required.",
        ],
        "scope": packet["scope"],
        "origin": "HUMAN_REVIEW",
        "reliability": None,
        "reviewed_by": "",
        "rationale": "",
        "stated_limitation": "",
        "basis": packet["basis"],
    }


def print_packet(name: str) -> int:
    packet = PACKETS.get(name)
    if packet is None:
        return _fail(f"no review packet named {name!r}. Known: {sorted(PACKETS)}")

    print("=" * 78)
    print(f"FACTUAL REVIEW PACKET — {name}")
    print("=" * 78)
    print("\nSCOPE (five parts, all required, matched in full or not at all):")
    for key, value in packet["scope"].items():
        print(f"  {key:20} {value}")
    print(f"\nFull review: {packet['review_document']}")
    print("\nWHAT EVIDENCE IN THIS SCOPE SUPPORTS:")
    print(f"  {packet['what_the_evidence_supports']}")
    print("\nMATERIAL FINDINGS you must consciously account for:")
    for i, finding in enumerate(packet["material_findings"], 1):
        print(f"  {i}. {finding}")
    print("\nRETRIEVED DOCUMENTS (facts, pre-filled in the template below):")
    for item in packet["basis"]:
        print(f"  [{item['basis_type']}] {item['document_title']}")
        print(f"      {item['summarized_finding']}")
    print("\n" + "=" * 78)
    print("NOTHING ABOVE PROPOSES A VALUE. The number, the rationale and the")
    print("limitation are yours, and the guide is docs/data/evidence-reliability-")
    print("review-guide-v1.md §3 (write the failure mode first) and §4.")
    print("=" * 78)
    print("\nTEMPLATE — save this, fill the blanks, then pass it with --review-file:\n")
    print(json.dumps(_template(packet), indent=2, ensure_ascii=False))
    return 0


def _build(review: dict[str, Any]) -> ReliabilityAssessment:
    """Validate the operator's file into an assessment, or raise.

    Every check here is about the FILE being complete. The model does the rest:
    range, calibration coupling, document-backed basis, supersession halves.
    """
    missing = [f for f in JUDGEMENT_FIELDS if review.get(f) in (None, "", [])]
    if missing:
        raise ValueError(
            f"the review file leaves {missing} empty. Every one is a judgement only the "
            "reviewer can make, and this tool has no default for any of them"
        )

    reviewed_by = str(review["reviewed_by"]).strip()
    # A placeholder is worse than a blank, because a blank is refused and a
    # placeholder is recorded. Found by real use in Mission 1.15.13, where the
    # reviewer pasted a template shape into the field that exists to say who is
    # accountable.
    if reviewed_by.startswith("<") or reviewed_by.startswith("["):
        raise ValueError(
            f"{reviewed_by!r} is a placeholder, not a name. `reviewed_by` is the field a "
            "later reader uses to ask who decided this; a template shape recorded there "
            "reads as an identity and answers nobody"
        )
    if reviewed_by.lower() in IMPERSONAL:
        raise ValueError(
            f"{reviewed_by!r} names nobody. `reviewed_by` is what a later reader uses to "
            "ask who decided this and why; the review guide §5 says it names a person, "
            "not a team, not a script, not a model"
        )

    reliability = review["reliability"]
    if isinstance(reliability, bool) or not isinstance(reliability, int | float):
        raise ValueError(f"reliability {reliability!r} is not a number")

    scope_raw = review.get("scope") or {}
    scope = ReliabilityScope(
        source_id=str(scope_raw.get("source_id", "")),
        resource_id=str(scope_raw.get("resource_id", "")),
        record_kind_id=str(scope_raw.get("record_kind_id", "")),
        claim_type=ClaimType(str(scope_raw.get("claim_type", ""))),
        proposition_kind=str(scope_raw.get("proposition_kind", "")),
    )

    basis = tuple(
        ReliabilityBasis(
            basis_type=ReliabilityBasisType(item["basis_type"]),
            document_title=item["document_title"],
            summarized_finding=item["summarized_finding"],
            document_url=item.get("document_url"),
            section_reference=item.get("section_reference"),
            excerpt=item.get("excerpt"),
            retrieved_at=(
                datetime.fromisoformat(item["retrieved_at"]) if item.get("retrieved_at") else None
            ),
        )
        for item in review.get("basis") or ()
    )

    origin = ReliabilityAssessmentOrigin(str(review.get("origin", "HUMAN_REVIEW")))
    return ReliabilityAssessment(
        id=str(uuid.uuid4()),
        scope=scope,
        version=1,
        reliability=float(reliability),
        origin=origin,
        rationale=str(review["rationale"]).strip(),
        stated_limitation=str(review["stated_limitation"]).strip(),
        reviewed_by=reviewed_by,
        reviewed_at=datetime.now(UTC),
        basis=basis,
        calibration_dataset_ref=review.get("calibration_dataset_ref"),
    )


def _next_version(conn: Any, assessment: ReliabilityAssessment) -> tuple[int, str | None]:
    """The version this becomes, and the current row it would supersede.

    Append-only: a later review is version N+1 and the previous current row is
    marked superseded. Nothing is updated in place, because an aggregation that
    used version N must still be able to read version N.
    """
    rows = conn.execute(
        "SELECT id, version FROM epistemic.reliability_assessments "
        "WHERE assessment_key = %s ORDER BY version DESC",
        (assessment.key,),
    ).fetchall()
    if not rows:
        return 1, None
    current = conn.execute(
        "SELECT id FROM epistemic.reliability_assessments "
        "WHERE assessment_key = %s AND superseded_at IS NULL",
        (assessment.key,),
    ).fetchone()
    return int(rows[0][1]) + 1, (str(current[0]) if current else None)


def _persist(conn: Any, assessment: ReliabilityAssessment, version: int, supersedes: str | None):
    now = datetime.now(UTC)
    if supersedes is not None:
        conn.execute(
            "UPDATE epistemic.reliability_assessments "
            "SET superseded_at = %s, superseded_by = %s, superseded_reason = %s "
            "WHERE id = %s",
            (now, assessment.id, f"superseded by version {version}", supersedes),
        )
    conn.execute(
        """INSERT INTO epistemic.reliability_assessments
               (id, assessment_key, version, source_id, resource_id, record_kind_registry,
                record_kind_id, claim_type, proposition_kind, reliability, origin,
                calibration_dataset_ref, rationale, stated_limitation, reviewed_by, reviewed_at)
           VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)""",
        (
            assessment.id,
            assessment.key,
            version,
            assessment.scope.source_id,
            assessment.scope.resource_id,
            RECORD_KIND_REGISTRY,
            assessment.scope.record_kind_id,
            assessment.scope.claim_type.value,
            assessment.scope.proposition_kind,
            assessment.reliability,
            assessment.origin.value,
            assessment.calibration_dataset_ref,
            assessment.rationale,
            assessment.stated_limitation,
            assessment.reviewed_by,
            assessment.reviewed_at,
        ),
    )
    for item in assessment.basis:
        conn.execute(
            """INSERT INTO epistemic.reliability_assessment_basis
                   (id, assessment_id, basis_type, document_title, document_url,
                    section_reference, summarized_finding, excerpt, retrieved_at)
               VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s)""",
            (
                str(uuid.uuid4()),
                assessment.id,
                item.basis_type.value,
                item.document_title,
                item.document_url,
                item.section_reference,
                item.summarized_finding,
                item.excerpt,
                item.retrieved_at,
            ),
        )


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--packet", help="print the factual review packet and a blank template")
    parser.add_argument("--review-file", help="the review file YOU filled in")
    parser.add_argument("--apply", action="store_true", help="persist after explicit confirmation")
    args = parser.parse_args()

    if args.packet:
        return print_packet(args.packet)
    if not args.review_file:
        return _fail("pass --packet <name> to start, or --review-file <path> to record one")

    path = pathlib.Path(args.review_file)
    if not path.exists():
        return _fail(f"{path} does not exist")
    try:
        review = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        return _fail(f"{path} is not valid JSON: {exc}")

    try:
        assessment = _build(review)
    except (ValueError, KeyError) as exc:
        return _fail(str(exc))

    url = os.environ.get("DATABASE_URL")
    if not url:
        return _fail("DATABASE_URL is not set. This writes to a deployment, not to the tree.")

    import psycopg

    with psycopg.connect(url) as conn:
        version, supersedes = _next_version(conn, assessment)

        print("=" * 78)
        print("ABOUT TO RECORD A RELIABILITY ASSESSMENT")
        print("=" * 78)
        for key, value in assessment.scope.to_json().items():
            print(f"  scope.{key:18} {value}")
        print(f"  origin              {assessment.origin.value}")
        print(
            f"  version             {version}"
            + (f"  (supersedes {supersedes})" if supersedes else "")
        )
        print(f"  reviewed_by         {assessment.reviewed_by}")
        print(f"  reliability         {assessment.reliability}")
        print(f"\n  rationale\n    {assessment.rationale}")
        print(f"\n  stated_limitation\n    {assessment.stated_limitation}")
        print(
            f"\n  basis               {len(assessment.basis)} row(s), "
            f"{sum(1 for b in assessment.basis if b.is_document_backed)} document-backed"
        )
        print("=" * 78)

        if not args.apply:
            print("\nDRY RUN. Nothing was written. Re-run with --apply to record it.")
            return 0

        print("\nRecording this states that the value above is YOUR judgement, reached")
        print("from the documents cited, and that you are accountable for it.")
        try:
            typed = input(f"\nType {CONFIRMATION!r} to record it, anything else to abort: ")
        except EOFError:
            return _fail(
                "no terminal to confirm on. A reliability assessment is a human decision "
                "and this is not a step a pipeline runs"
            )
        if typed.strip().lower() != CONFIRMATION:
            print("aborted. Nothing was written.")
            return 1

        _persist(conn, assessment, version, supersedes)
        conn.commit()
        print(f"\nrecorded. assessment {assessment.id}, version {version}")
        return 0


if __name__ == "__main__":
    raise SystemExit(main())
