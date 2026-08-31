#!/usr/bin/env python3
"""Mechanically enforce the compliance-capability rules.

Mission 1.4 §42, §43. Runs with **nothing installed** and needs no database,
like the source-registry validator and for the same reason (ADR-009): this is
the check that stands between an approving review and a collector, and a check
that cannot run because a dependency failed to install is a check that gets
skipped.

Checked:
  1. The compliance configuration parses and every record validates.
  2. No credential value appears anywhere in it.
  3. Every condition on every approving review resolves to a real verifier --
     no condition names a capability nobody built.
  4. Every compliance entry targets its source's CURRENT review version.
  5. No compliance entry exists for a source with no approving review.
  6. Every registered capability's conformance check passes.
  7. Every exact required notice appears verbatim in the evidence that
     established it, so nobody can quietly reword one.
  8. Every resource scope denies unknown content origin and excludes something.
  9. A HUMAN_CONFIRMATION condition cannot be satisfied by any verifier.
 10. An ineligible source produces no acquisition authorization.
 11. The network boundary is one file, and no governance package holds a
     collector (narrowed in Mission 1.5, when the first collector arrived).

Usage: python infrastructure/scripts/validate_compliance_capabilities.py
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

from sros_acquisition.compliance import (  # noqa: E402
    CAPABILITIES,
    AcquisitionNotAuthorizedError,
    build_authorization,
    capability_failures,
    find_compliance_config,
    load_compliance,
    satisfied_condition_keys,
    verify_condition,
    verify_source,
)
from sros_acquisition.registry import (  # noqa: E402
    APPROVING_STATES,
    ReviewCondition,
    SourceRegistryError,
    evaluate_eligibility,
    load_catalog,
)
from sros_contracts import (  # noqa: E402
    AttributionElement,
    ConditionVerification,
    ConditionVerificationResult,
)

DEFAULT_CATALOG = ROOT / "docs" / "data" / "source-catalog-v1.json"
DEFAULT_COMPLIANCE = ROOT / "docs" / "data" / "source-compliance-v1.json"

# Same shapes the catalog validator refuses. The compliance configuration is the
# second file a credential could reach, and it is read by the same people.
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


def main(argv: list[str]) -> int:
    catalog_path = pathlib.Path(argv[1]) if len(argv) > 1 else DEFAULT_CATALOG
    compliance_path = (
        pathlib.Path(argv[2])
        if len(argv) > 2
        else (DEFAULT_COMPLIANCE if DEFAULT_COMPLIANCE.exists() else find_compliance_config())
    )
    errors: list[str] = []
    now = datetime.now(UTC)

    # -- 2: textual scan, before parsing --------------------------------------
    raw = compliance_path.read_text(encoding="utf-8")
    for pattern, description in SECRET_PATTERNS:
        if pattern.search(raw):
            errors.append(
                f"the compliance configuration contains what looks like {description}. It "
                "holds configuration KEY NAMES and required notices, never a secret"
            )
    print(f"ok    no credential value in {compliance_path.name}")

    # -- 1: both files parse ---------------------------------------------------
    try:
        catalog = load_catalog(catalog_path)
        config = load_compliance(compliance_path)
    except (SourceRegistryError, ValueError) as exc:
        print(f"FAIL  configuration does not validate: {exc}", file=sys.stderr)
        return 1
    print(
        f"ok    compliance configuration parses ({len(config)} source(s), "
        f"version {config.compliance_version})"
    )

    catalog_ids = {s.source_id for s in catalog}

    # Mission 1.15.5. A compliance entry configures a source FOR A USE, so both
    # checks below ask about the review under the entry's own profile. Asking
    # `source.review` would compare against the legacy profile whatever the
    # entry said, which is the source-only reasoning this mission removed --
    # and it reported TED's local entry as preparation for an approval that
    # already exists under the profile it names.
    def profile_review(entry):
        source = next((s for s in catalog if s.source_id == entry.source_id), None)
        return source.review_for(entry.use_profile_id) if source else None

    # Mission 1.15.6. Checks 3, 6, 9 and 10 below walked `source.review` -- the
    # LEGACY profile's review and nothing else -- which was correct while every
    # review answered one profile. TED's local review is the first that does
    # not, so a condition, a capability or an authorization existing only under
    # a second profile was checked by nothing here. Walking the pairs is what
    # `reviews_by_profile` was built for.
    pairs = [
        (source, profile, review)
        for source in catalog
        for profile, review in source.reviews_by_profile().items()
    ]

    # -- 5: no entry for a source/profile pair that has not been approved ------
    for entry in config:
        if entry.source_id not in catalog_ids:
            errors.append(f"{entry.source_id}: a compliance entry for a source not in the catalog")
            continue
        review = profile_review(entry)
        if review is None or review.approval_state not in APPROVING_STATES:
            errors.append(
                f"{entry.source_id}: a compliance entry for a source with no approving "
                f"review under use profile {entry.use_profile_id!r}. Compliance "
                "parameters for a use nobody approved read as preparation for "
                "approving it"
            )

    # -- 4: entries target the current review OF THEIR PROFILE ----------------
    for entry in config:
        review = profile_review(entry)
        if review is None:
            continue
        if entry.review_version != review.review_version:
            errors.append(
                f"{entry.source_id}: the compliance entry targets review version "
                f"{entry.review_version} and the current review under use profile "
                f"{entry.use_profile_id!r} is version {review.review_version}"
            )

    # -- 8: every scope fails closed on unknown origin, and excludes something --
    for entry in config:
        scope = entry.resource_scope
        if not scope.third_party_denied:
            errors.append(
                f"{entry.source_id}: third-party content is permitted. Every source "
                "approved so far republishes material it does not own, and UNKNOWN "
                "origin must fail closed where licensing scope matters (§12)"
            )
        restrictions = (
            scope.licence_allowlist,
            scope.geography_allowlist,
            scope.excluded_dataset_families or None,
            scope.enumerated_exclusions or None,
            scope.excluded_note_markers or None,
            # `require_dataset_family` denies any resource whose family is
            # unrecorded, which is a resource-level restriction by any reading.
            # It was missing from this tuple because World Bank -- the only
            # source that had ever set it -- also carries an exclusion list, so
            # the omission never showed. GDELT sets it alone: its grant covers
            # everything it releases equally, so there is no licence or family
            # to exclude, and what the review DID limit is which of GDELT's
            # products were looked at.
            scope.require_dataset_family or None,
        )
        if not any(restrictions):
            errors.append(
                f"{entry.source_id}: the resource scope restricts nothing beyond content "
                "origin. A scope that restricts nothing is a source-level approval "
                "wearing a resource-level name"
            )
        if not entry.data_minimisation.excluded:
            errors.append(
                f"{entry.source_id}: the data-minimisation profile excludes no category. "
                "A profile that excludes nothing minimises nothing (§31)"
            )
    print("ok    every resource scope fails closed and restricts something")

    # -- 6: every registered capability is genuinely implemented ---------------
    # Each capability is checked against the sources whose conditions actually
    # name it. Running every capability against every source would fail on
    # configuration that legitimately does not exist -- FRED has no geography
    # allowlist because its terms impose none.
    unused = set(CAPABILITIES)
    for source, profile, review in pairs:
        entry = config.get(source.source_id, profile)
        if entry is None:
            continue
        for condition in review.required_conditions:
            if condition.verification is not ConditionVerification.CAPABILITY:
                continue
            name = (condition.verification_detail or "").strip()
            unused.discard(name)
            failures = capability_failures(name, entry)
            if failures is None:
                errors.append(
                    f"{source.source_id}/{condition.key}: names capability {name!r}, which "
                    "is not registered. A condition whose verifier does not exist has not "
                    "been checked (§43.2)"
                )
            elif failures:
                errors.append(
                    f"{source.source_id}/{condition.key}: capability {name!r} fails its "
                    f"conformance check: {'; '.join(failures)}"
                )
    if unused:
        errors.append(
            f"registered capabilities that no condition names: {sorted(unused)}. §5 forbids "
            "unused abstractions; a capability nothing requires is one nobody checks"
        )
    print(f"ok    every capability a condition names is implemented ({len(CAPABILITIES)} total)")

    # -- 3: every condition resolves to a verifier, or is an explicit gap -------
    #
    # UNKNOWN has two causes and only one of them is a defect. Until Mission 1.7
    # no approving review carried a HUMAN_CONFIRMATION condition, so the two
    # were indistinguishable here and the check treated both as errors:
    #
    #   * a condition naming a CAPABILITY or ACCESS_METHOD that does not exist
    #     is a defect. It names something unreal and will resolve UNKNOWN for
    #     ever, which is a condition nobody is checking dressed as one somebody
    #     is;
    #   * a HUMAN_CONFIRMATION condition resolves UNKNOWN **by design**
    #     (`acquisition-authorization-v1.md`, §21): no verifier can establish it
    #     and none in this repository writes one. It still blocks eligibility,
    #     which is the point -- it is the honest answer for an obligation a
    #     program cannot check, and `source-review-guide.md` §9 requires it
    #     rather than a machine-checkable reword of a legal judgment.
    #
    # Rejecting the second would force every such obligation into prose, which
    # is exactly what Mission 1.7 §28 forbids.
    unresolved: list[str] = []
    human: list[str] = []
    for source, profile, review in pairs:
        if review.approval_state not in APPROVING_STATES:
            continue
        records = verify_source(source, profile, config, environ={}, now=now)
        if len(records) != len(review.required_conditions):
            errors.append(
                f"{source.source_id}/{profile}: not every condition produced a verification"
            )
        for record in records:
            if record.result is not ConditionVerificationResult.UNKNOWN:
                continue
            if record.verification is ConditionVerification.HUMAN_CONFIRMATION:
                human.append(f"{source.source_id}/{profile}/{record.condition_key}")
            else:
                unresolved.append(
                    f"{source.source_id}/{profile}/{record.condition_key}: {record.reason}"
                )
    if unresolved:
        errors.append(
            "condition(s) whose verifier does not exist:\n      " + "\n      ".join(unresolved)
        )
    print(
        "ok    every condition on an approving review resolves to a verifier "
        f"({len(human)} awaiting a human decision, which block)"
    )

    # -- 7: exact notices are traceable to the evidence that established them --
    for entry in config:
        review = profile_review(entry)
        if review is None:
            continue
        requirement = entry.attribution.requirement(AttributionElement.EXACT_NOTICE)
        if requirement is None:
            continue
        # The trailing full stop is normalised away: the review quoted the
        # sentence inside its own prose, where it does not carry one. Nothing
        # else about the wording is normalised, on purpose.
        notice = (requirement.text or "").strip().rstrip(".")
        corpus = " ".join(
            (item.summarized_finding or "") + " " + (item.excerpt or "") for item in review.evidence
        )
        if notice and notice not in corpus:
            errors.append(
                f"{entry.source_id}: the exact required notice does not appear in any "
                "evidence record for the current review. A prescribed sentence has to be "
                "traceable to the document that prescribed it, or it is our wording"
            )
    print("ok    every exact required notice is traceable to its evidence")

    # -- 9: no verifier satisfies a human condition ----------------------------
    #
    # Probed against every approving source rather than one: the branch is
    # reached before any per-source configuration is consulted, and asserting it
    # everywhere costs nothing while a single sample would leave the question
    # "was it the source that made the difference" open.
    probe = ReviewCondition(
        key="validator-probe",
        description="A probe asserting that no verifier can satisfy a human condition.",
        verification=ConditionVerification.HUMAN_CONFIRMATION,
    )
    for source, profile, _ in pairs:
        outcome = verify_condition(
            source, profile, probe, config.get(source.source_id, profile), {}, now
        )
        if outcome.result is not ConditionVerificationResult.UNKNOWN:
            errors.append(
                f"{source.source_id}/{profile}: a HUMAN_CONFIRMATION condition resolved "
                f"to {outcome.result.value}. Only a person may record one, and no "
                "verifier may reach any other answer (§21)"
            )
    print("ok    a human-confirmation condition cannot be satisfied by any verifier")

    # -- 10: an ineligible source produces no authorization --------------------
    authorized: list[str] = []
    for source, profile, _ in pairs:
        records = verify_source(source, profile, config, environ={}, now=now)
        eligible = evaluate_eligibility(
            source, profile, now, satisfied_condition_keys(list(records))
        )
        try:
            context = build_authorization(source, profile, config, records, environ={}, now=now)
        except AcquisitionNotAuthorizedError:
            if eligible.eligible:
                errors.append(
                    f"{source.source_id}/{profile}: passes the gate and yet no "
                    "authorization can be built. The two must agree, or the gate is "
                    "reporting something the boundary does not honour"
                )
            continue
        authorized.append(f"{source.source_id}/{profile}")
        if not eligible.eligible:
            errors.append(
                f"{source.source_id}/{profile}: an acquisition authorization was built "
                "for a source the gate refuses. This is the one thing §27 exists to "
                "prevent"
            )
        # Mission 1.15.6 §22. Where a route restriction was reviewed, the context
        # must carry the reviewed routes and nothing else. A blocked route
        # reaching a collector would make the restriction advisory.
        entry = config.get(source.source_id, profile)
        routes = entry.route_authorization if entry else None
        if routes is not None:
            carried = set(context.authorized_route_labels)
            if carried != set(routes.allowed_labels):
                errors.append(
                    f"{source.source_id}/{profile}: the authorization carries routes "
                    f"{sorted(carried)} and the review authorised "
                    f"{sorted(routes.allowed_labels)}"
                )
    print(
        f"ok    authorization follows the gate exactly "
        f"({len(authorized)} of {len(pairs)} (source, use profile) pair(s) authorizable "
        "with no credentials configured)"
    )

    # -- 11: the collection boundary holds ------------------------------------
    #
    # Mission 1.4 asserted here that no collector and no network client existed
    # anywhere in this package. Mission 1.5 built one, so the check was NARROWED
    # rather than deleted -- the same move Mission 1.2 made with the D-03 guard.
    # Naming the one file that may reach a network, and the packages that may
    # not hold a collector, says more than asserting both are absent.
    package = ROOT / "services" / "acquisition" / "python" / "sros_acquisition"
    network_boundary = package / "collection" / "transport.py"
    forbidden = re.compile(
        r"^\s*(?:import|from)\s+(?:requests|httpx|urllib|aiohttp|http\.client|socket|"
        r"playwright|selenium)",
        re.MULTILINE,
    )
    for file in sorted(package.rglob("*.py")):
        if file == network_boundary:
            continue
        if forbidden.search(file.read_text(encoding="utf-8")):
            errors.append(
                f"{file.relative_to(package)} imports a network client. The boundary is "
                "collection/transport.py and nothing else"
            )
    if not network_boundary.exists():
        errors.append(
            "collection/transport.py is missing, so the network boundary this check "
            "pins does not exist"
        )
    # The registry DECIDES whether a source may be collected from; the compliance
    # layer says what a collector must obey. A collector in either would put the
    # decision and its execution in the same place.
    for governance in ("registry", "compliance"):
        for file in sorted((package / governance).rglob("*collector*.py")):
            errors.append(f"{file.relative_to(package)} is a collector inside a governance package")
    print(
        "ok    the network boundary is collection/transport.py, and no governance "
        "package holds a collector"
    )

    if errors:
        print(f"\nCOMPLIANCE VALIDATION FAILED ({len(errors)} problem(s)):", file=sys.stderr)
        for error in errors:
            print(f"  - {error}", file=sys.stderr)
        return 1

    # Counted per (source, profile) since Mission 1.15.5: a source approved
    # under two profiles carries two sets of conditions, and one number for
    # the source would hide which use they belong to.
    pairs = [
        (source, review) for source in catalog for review in source.reviews_by_profile().values()
    ]
    conditions = sum(len(review.required_conditions) for _, review in pairs)
    approving_pairs = [pair for pair in pairs if pair[1].approval_state in APPROVING_STATES]
    print(
        "\ncompliance validation passed: "
        f"{conditions} condition(s) across {len(approving_pairs)} approving "
        f"(source, use profile) pair(s), {len(CAPABILITIES)} capabilities, "
        f"{len(authorized)} authorizable"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
