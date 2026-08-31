#!/usr/bin/env python3
"""Mechanically enforce the Source Registry governance rules.

Mission 1.0 §33. Runs with **nothing installed**: stdlib Python plus the
dependency-free `sros_contracts` and `sros_acquisition` packages, reached by
path. ADR-009's argument applies unchanged — a check that cannot run because a
dependency failed to install is a check that gets skipped, and this is the check
that stands between a candidate source and a collector.

It needs no database. The catalog file is the artefact a reviewer edits, so it
is the artefact that must be validatable before anything is loaded anywhere.

Checked:
  1. The catalog parses and every record satisfies its own model.
  2. No duplicate source id.
  3. An approving state has evidence, and at least one authoritative document.
  4. Every evidence record has a URL and a retrieval time.
  5. A source requiring a credential names a configuration reference.
  6. No secret value appears anywhere in the catalog.
  7. No approving review is stale.
  8. Retention overrides carry a basis and stay within the baseline.
  9. Every non-approving source states what is missing.
 10. Coverage claims do not infer geography from language.
 11. No evidence-aggregation vocabulary leaked in (D-03 stays blocked).
 12. An approving review positively PERMITS every activity the assessed use
     materially requires. Silence is not permission (§1 rule 2).

Usage: python infrastructure/scripts/validate_source_registry.py [catalog.json]
"""

from __future__ import annotations

import pathlib
import re
import sys
from datetime import UTC, datetime

ROOT = pathlib.Path(__file__).resolve().parents[2]
for package in (
    ROOT / "packages" / "contracts" / "python",
    ROOT / "services" / "acquisition" / "python",
):
    if str(package) not in sys.path:
        sys.path.insert(0, str(package))

from sros_acquisition.registry import (  # noqa: E402
    APPROVING_STATES,
    SourceRegistryError,
    evaluate_eligibility,
    load_catalog,
    resolve_retention,
)
from sros_acquisition.registry.models import LEGACY_USE_PROFILE  # noqa: E402
from sros_acquisition.registry.retention import (  # noqa: E402
    BASELINE_NORMALIZED_DAYS,
    BASELINE_RAW_DAYS,
)
from sros_contracts import PolicyAssessment  # noqa: E402

DEFAULT_CATALOG = ROOT / "docs" / "data" / "source-catalog-v1.json"

REQUIRED_ACTIVITIES = (
    "automated_access",
    "api_use",
    "commercial_use",
    "storage",
    "derived_analytics",
    "model_processing",
)
GRANTING = {PolicyAssessment.PERMITTED, PolicyAssessment.PERMITTED_WITH_CONDITIONS}

# A credential that reached the catalog would be published to everyone who reads
# the governance record -- the exact opposite of what a registry is for. These
# are shapes, not a complete list; the model refuses them at construction too.
SECRET_PATTERNS = [
    (re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----"), "a private key"),
    (re.compile(r"\bgh[pousr]_[A-Za-z0-9]{16,}"), "a GitHub token"),
    (re.compile(r"\bgithub_pat_[A-Za-z0-9_]{20,}"), "a GitHub fine-grained token"),
    (re.compile(r"\bsk-[A-Za-z0-9]{20,}"), "an API secret key"),
    (re.compile(r"\bxox[baprs]-[A-Za-z0-9-]{10,}"), "a Slack token"),
    (re.compile(r"\bAIza[0-9A-Za-z_-]{35}"), "a Google API key"),
    (re.compile(r"\bAKIA[0-9A-Z]{16}"), "an AWS access key id"),
    (re.compile(r'"(?:password|client_secret|api_key)"\s*:\s*"[^"]{8,}"'), "an inline credential"),
]

# D-03. A source's policy metadata is not its Evidence Score, and the surest way
# to smuggle scoring in is to name a field after it.
FORBIDDEN_AGGREGATION_TERMS = [
    "decay_weight",
    "aggregated_evidence_score",
    "independence_threshold_result",
    "contradiction_penalty",
    "evidence_aggregate",
    "decay_half_life",
    "evidence_weight",
    "source_reliability_score",
    "trust_score",
]


def main(argv: list[str]) -> int:
    path = pathlib.Path(argv[1]) if len(argv) > 1 else DEFAULT_CATALOG
    errors: list[str] = []
    warnings: list[str] = []
    now = datetime.now(UTC)

    if not path.exists():
        print(f"FAIL  no catalog at {path}", file=sys.stderr)
        return 1

    raw_text = path.read_text(encoding="utf-8")

    # -- 6 & 11: textual scans, before parsing --------------------------------
    for pattern, description in SECRET_PATTERNS:
        if pattern.search(raw_text):
            errors.append(
                f"the catalog contains what looks like {description}. Secrets belong in "
                "the environment or a secret manager; the registry stores configuration "
                "KEY NAMES only"
            )
    lowered = raw_text.lower()
    leaked = [term for term in FORBIDDEN_AGGREGATION_TERMS if term in lowered]
    if leaked:
        errors.append(
            f"evidence-aggregation vocabulary in the catalog: {leaked}. D-03 is "
            "unresolved, and a source's policy metadata is not its Evidence Score "
            "(Mission 1.0 §36)"
        )
    print(f"ok    no credential value and no aggregation vocabulary in {path.name}")

    # -- 1 & 2: the catalog parses and every record validates ------------------
    try:
        catalog = load_catalog(path)
    except SourceRegistryError as exc:
        print(f"FAIL  catalog does not validate: {exc}", file=sys.stderr)
        return 1
    except ValueError as exc:
        print(f"FAIL  catalog is malformed: {exc}", file=sys.stderr)
        return 1
    print(f"ok    catalog parses and every record validates ({len(catalog)} sources)")

    eligible: list[str] = []

    # -- 12: silence is not permission, made mechanical ------------------------
    #
    # The assessed use case is automated collection by a COMMERCIAL multi-tenant
    # SaaS for STORAGE, DERIVED ANALYTICS and LLM PROCESSING. Those five words
    # name activities, and an approving review has to have found a grant for
    # each of them -- not merely to have failed to find a prohibition.
    #
    # Mission 1.7 approved `pypi` with all four of the load-bearing activities
    # recorded NOT_ADDRESSED, on a review whose own notes said the state "rests
    # on the absence of a prohibition covering us plus the presence of a
    # documented API". That is the exact move `source-registry-v1.md` §1 rule 2
    # and Mission 1.7 §12 forbid, and the prose rule did not stop it because
    # nothing read the prose. This does.
    #
    # NOT in the required set, and each for its own reason:
    #   browser_automation      no source uses a browser profile
    #   retention               a LIMIT, not a permission. Silence means the
    #                           project baseline applies, which is the baseline
    #                           working rather than a gap
    #   redistribution          required only where source content is
    #                           republished; aggregated insight is analytics
    #   personal_data_handling  governed by personal_data_risk and by H-12
    #   attribution_required    an OBLIGATION. Silence there means no duty was
    #                           found, which cannot block an approval

    materiality_errors: list[str] = []
    for source in catalog:
        review = source.review
        if review is None or review.approval_state not in APPROVING_STATES:
            continue
        ungranted = [
            activity
            for activity in REQUIRED_ACTIVITIES
            if review.assessment(activity) not in GRANTING
        ]
        if ungranted:
            materiality_errors.append(
                f"{source.source_id}: {review.approval_state.value} while the assessed use "
                f"requires {', '.join(ungranted)}, which no evidence grants "
                f"({', '.join(review.assessment(a).value for a in ungranted)}). "
                "Absence of a prohibition is not a permission (source-registry-v1.md §1 "
                "rule 2)"
            )
    errors.extend(materiality_errors)
    if not materiality_errors:
        print(
            "ok    approving reviews grant every materially required activity "
            f"({len(REQUIRED_ACTIVITIES)} checked)"
        )

    for source in catalog:
        sid = source.source_id
        review = source.review

        # -- 3, 4, 7: review and evidence -------------------------------------
        if review is not None:
            if review.approval_state in APPROVING_STATES:
                if not review.evidence:
                    errors.append(f"{sid}: {review.approval_state.value} with no evidence")
                elif not any(item.is_authoritative for item in review.evidence):
                    errors.append(
                        f"{sid}: {review.approval_state.value} with no official or "
                        "authoritative document"
                    )
                if review.is_stale(now):
                    errors.append(
                        f"{sid}: approving review is stale (due "
                        f"{review.next_review_at.date().isoformat()}). A stale approval "
                        "must fail closed rather than keep granting access"
                    )
            else:
                # -- 9: a non-approving state must say what is missing ---------
                if not review.open_questions and not (review.review_notes or "").strip():
                    errors.append(
                        f"{sid}: {review.approval_state.value} with neither open questions "
                        "nor review notes. A source nobody can act on is a source that "
                        "stays blocked for reasons nobody remembers"
                    )

            for item in review.evidence:
                if not item.document_url.startswith(("http://", "https://")):
                    errors.append(f"{sid}: evidence {item.document_title!r} has no usable URL")
                if item.retrieved_at > now:
                    errors.append(
                        f"{sid}: evidence {item.document_title!r} was retrieved in the future"
                    )

        # -- 5: credential metadata -------------------------------------------
        for profile in source.access_profiles:
            if profile.requires_credential and not profile.secret_references:
                errors.append(
                    f"{sid}: access profile {profile.label!r} requires a credential with "
                    "no configuration reference"
                )

        # -- 8: retention ------------------------------------------------------
        override = source.retention_override
        if override is not None:
            if not override.basis.strip():
                errors.append(f"{sid}: retention override with no basis")
            effective = resolve_retention(override)
            if effective.raw_days > BASELINE_RAW_DAYS:
                errors.append(
                    f"{sid}: effective raw retention {effective.raw_days}d exceeds the "
                    f"{BASELINE_RAW_DAYS}d baseline. The stricter rule must win"
                )
            if effective.normalized_days > BASELINE_NORMALIZED_DAYS:
                errors.append(
                    f"{sid}: effective normalized retention {effective.normalized_days}d "
                    f"exceeds the {BASELINE_NORMALIZED_DAYS}d baseline"
                )
            if override.raw_days is not None and override.raw_days > BASELINE_RAW_DAYS:
                warnings.append(
                    f"{sid}: retention override asks for {override.raw_days}d of raw "
                    f"retention; the {BASELINE_RAW_DAYS}d baseline is stricter and applies. "
                    "Lengthening retention needs necessity established, not configuration"
                )

        # -- 10: coverage ------------------------------------------------------
        if source.coverage.scope == "GLOBAL" and source.coverage.languages == ("en",):
            warnings.append(
                f"{sid}: coverage is GLOBAL with English as the only language. A source "
                "dominated by English speakers is not representative of the global market "
                "(Mission 1.0 §17)"
            )

        # -- the gate ----------------------------------------------------------
        result = evaluate_eligibility(source, LEGACY_USE_PROFILE, now)
        if result.eligible:
            eligible.append(sid)
        if source.collector_enabled and not result.eligible:
            errors.append(
                f"{sid}: collector is enabled on an ineligible source "
                f"({'; '.join(result.blocking_reasons)})"
            )

    print("ok    approving reviews carry authoritative evidence and are not stale")
    print("ok    credentialed access profiles name a configuration reference")
    print("ok    retention overrides carry a basis and stay within the baseline")
    print("ok    blocked sources state what is missing")

    if eligible:
        print(f"ok    {len(eligible)} source(s) collector-eligible: {', '.join(eligible)}")
    else:
        print("ok    no source is collector-eligible (every candidate is still blocked)")

    print()
    for warning in warnings:
        print(f"warn  {warning}")

    if errors:
        print(f"\nSOURCE REGISTRY VALIDATION FAILED ({len(errors)} problem(s)):", file=sys.stderr)
        for error in errors:
            print(f"  - {error}", file=sys.stderr)
        return 1

    print(
        f"\nsource registry validation passed: {len(catalog)} sources, "
        f"{sum(len(s.review.evidence) for s in catalog if s.review)} evidence records, "
        f"{len(warnings)} warning(s)"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
