"""Rendering the human-readable catalog from the machine-readable one.

Mission 1.0 §41. The markdown table in `docs/data/source-catalog-v1.md` is
GENERATED from `source-catalog-v1.json` and checked in CI, for the reason
ADR-009 gives about contracts: two hand-maintained copies of one fact drift, and
the drift is discovered by whoever trusted the wrong one.

§41 also says not to hide uncertainty behind vague prose. So the renderer prints
the assessment values verbatim -- `NOT_ADDRESSED` stays `NOT_ADDRESSED` -- and
never softens them into a summary word.
"""

from __future__ import annotations

from datetime import UTC, datetime

from .registry import SourceCatalog, evaluate_eligibility, resolve_retention

__all__ = ["render_catalog_markdown"]

_ABBREVIATIONS = {
    "PERMITTED": "permitted",
    "PERMITTED_WITH_CONDITIONS": "conditional",
    "NOT_PERMITTED": "**not permitted**",
    "NOT_ADDRESSED": "not addressed",
    "UNCLEAR": "unclear",
    "NOT_ASSESSED": "not assessed",
}


def _cell(value: str) -> str:
    return _ABBREVIATIONS.get(value, value)


def render_catalog_markdown(catalog: SourceCatalog) -> str:
    now = datetime.now(UTC)
    results = {s.source_id: evaluate_eligibility(s, now) for s in catalog}
    eligible = [s for s in catalog if results[s.source_id].eligible]

    by_state: dict[str, list[str]] = {}
    for source in catalog:
        if source.review:
            by_state.setdefault(source.review.approval_state.value, []).append(source.source_id)

    lines: list[str] = []
    add = lines.append

    add("# Source Catalog V1")
    add("")
    add("**Status:** Authoritative record of the initial candidate catalog.")
    add(f"**Catalog version:** {catalog.catalog_version}")
    add(f"**Reviewed:** {catalog.review_date} by `{catalog.reviewer}`")
    add("**Governed by:** [`source-registry-v1.md`](source-registry-v1.md)")
    add("")
    add("> **GENERATED FILE.** Rendered from `source-catalog-v1.json` by")
    add("> `sros-source render`, and checked in CI. Edit the JSON, not this file.")
    add("")
    add("---")
    add("")
    add("## The assessed use case")
    add("")
    add("Every assessment below is scoped to one use, stated once:")
    add("")
    add(f"> {catalog.assessed_use_case}")
    add("")
    add(
        "An assessment does not transfer. A source that permits academic research "
        "has not permitted this, and a permission granted for a narrower purpose "
        "does not widen to cover it."
    )
    add("")
    add("## Summary")
    add("")
    add("| Approval state | Sources |")
    add("|----------------|---------|")
    for state in (
        "APPROVED",
        "APPROVED_WITH_CONDITIONS",
        "REQUIRES_REVIEW",
        "RESTRICTED",
        "PROHIBITED",
        "SUSPENDED",
        "DRAFT",
    ):
        ids = by_state.get(state, [])
        add(f"| `{state}` | {len(ids)}{' — ' + ', '.join(ids) if ids else ''} |")
    add("")
    add(f"**Collector-eligible from the catalog alone: {len(eligible)} of {len(catalog)}.**")
    add("")
    add(
        "This document is the **catalog view**: what the reviews say, with no condition "
        "verified. It is generated from a JSON file and committed, so it cannot depend "
        "on the machine it was rendered on -- and whether a condition holds depends on "
        "what is deployed and configured. A catalog can never assert its own conditions "
        "satisfied, so every source carrying one is shown blocked here."
    )
    add("")
    add(
        "For the environment view -- the same reviews with the verifiers actually run -- "
        "use `sros-source eligibility` or `sros-source conditions <source>`. The two can "
        "legitimately disagree, and only the second answers *may a collector run here*."
    )
    add("")
    add(
        "Either way, **no collector exists** and `collector_enabled` is false for every "
        "source. Passing the gate says a collector MAY be built."
    )
    add("")

    if catalog.known_limitations:
        add("### Limitations of this review")
        add("")
        for limitation in catalog.known_limitations:
            add(f"- {limitation}")
        add("")

    add("---")
    add("")
    add("## Assessment table")
    add("")
    add(
        "Activities are assessed separately, because their conditions differ. A source "
        "may permit automated API access and forbid commercial use, and only a "
        "per-activity reading can say so."
    )
    add("")
    add(
        "| Source | Family | Access | Official API | Auth | Commercial | Automation | "
        "Storage | Retention | Redistribution | Rate limits | Personal data | State | "
        "Eligible |"
    )
    add("|---|---|---|---|---|---|---|---|---|---|---|---|---|---|")
    for source in catalog:
        review = source.review
        result = results[source.source_id]
        methods = sorted({p.access_method.value for p in source.access_profiles})
        official = "yes" if any("OFFICIAL_API" in m or "PUBLIC_API" in m for m in methods) else "no"
        auth = "yes" if any(p.requires_authentication for p in source.access_profiles) else "no"
        limits = (
            "documented" if any(p.rate_limit_known for p in source.access_profiles) else "UNKNOWN"
        )
        state = review.approval_state.value if review else "NO REVIEW"
        add(
            f"| `{source.source_id}` | {source.source_family} | "
            f"{', '.join(m.replace('_', ' ').lower() for m in methods) or '-'} | {official} | {auth} | "
            f"{_cell(review.assessment('commercial_use').value) if review else '-'} | "
            f"{_cell(review.assessment('automated_access').value) if review else '-'} | "
            f"{_cell(review.assessment('storage').value) if review else '-'} | "
            f"{_cell(review.assessment('retention').value) if review else '-'} | "
            f"{_cell(review.assessment('redistribution').value) if review else '-'} | "
            f"{limits} | "
            f"{review.personal_data_risk.value if review else '-'} | "
            f"`{state}` | {'yes' if result.eligible else '**no**'} |"
        )
    add("")
    add("---")
    add("")
    add("## Per-source detail")
    add("")

    for source in catalog:
        review = source.review
        result = results[source.source_id]
        retention = resolve_retention(source.retention_override)

        add(f"### {source.canonical_name} — `{source.source_id}`")
        add("")
        add(f"{source.description}")
        add("")
        add(f"- **Family:** {source.source_family}")
        add(
            f"- **Coverage:** {source.coverage.scope}"
            + (
                f", countries {list(source.coverage.countries)}"
                if source.coverage.countries
                else ""
            )
            + (
                f", languages {list(source.coverage.languages)}"
                if source.coverage.languages
                else ""
            )
        )
        add(
            f"- **Retention if collected:** raw {retention.raw_days}d "
            f"({retention.raw_source}), normalized {retention.normalized_days}d "
            f"({retention.normalized_source})"
        )
        if retention.basis:
            add(f"  - Basis: {retention.basis}")
        add(
            f"- **State:** `{review.approval_state.value if review else 'NO REVIEW'}` — "
            f"**collector eligible from the catalog alone: "
            f"{'yes' if result.eligible else 'no'}**"
        )
        if review:
            add(
                f"- **Last reviewed:** {review.reviewed_at.date()} · next {review.next_review_at.date()}"
            )
        add("")

        # The history, not only the current verdict. Mission 1.3 §27: what a
        # reader needs in order to trust a verdict is what the previous one said
        # and why it changed.
        if len(source.review_history) > 1:
            add("**Review history**")
            add("")
            add("| Version | Reviewed | By | State | Evidence |")
            add("|---|---|---|---|---|")
            for past in source.review_history:
                marker = " ← current" if past is review else ""
                add(
                    f"| {past.review_version}{marker} | {past.reviewed_at.date()} | "
                    f"`{past.reviewed_by}` | `{past.approval_state.value}` | "
                    f"{len(past.evidence)} |"
                )
            add("")

        if review and review.required_conditions:
            add("**Required conditions** — all must be satisfied before a collector may run")
            add("")
            add("| Key | Verified by | Checks | Condition |")
            add("|---|---|---|---|")
            for condition in review.required_conditions:
                detail = (
                    f"`{condition.verification_detail}`" if condition.verification_detail else "—"
                )
                add(
                    f"| `{condition.key}` | `{condition.verification.value}` | {detail} | "
                    f"{condition.description} |"
                )
            add("")
            add(
                "None of these is satisfied *by the catalog*, and none can be: "
                "satisfaction is environment state, recorded by a verifier that says "
                "what it checked (`sros-source verify`). `APPROVED_WITH_CONDITIONS` "
                "means a collector MAY be designed, never that one may run."
            )
            add("")

        add("**Access profiles** (how, not whether)")
        add("")
        if source.access_profiles:
            add("| Method | Label | Requires | Secret references | Rate limit | Cost |")
            add("|---|---|---|---|---|---|")
            for profile in source.access_profiles:
                needs = [
                    n
                    for n, f in (
                        ("auth", profile.requires_authentication),
                        ("api key", profile.requires_api_key),
                        ("oauth", profile.requires_oauth),
                        ("account", profile.requires_account),
                        ("dev app", profile.requires_developer_app),
                        ("approval", profile.requires_approval),
                    )
                    if f
                ]
                limit = (
                    f"{profile.rate_limit_requests}/{profile.rate_limit_period_seconds}s "
                    f"({(profile.rate_limit_origin or '').lower()})"
                    if profile.rate_limit_known
                    else "**UNKNOWN**"
                )
                refs = ", ".join(f"`{r}`" for r in profile.secret_references) or "—"
                add(
                    f"| `{profile.access_method.value}` | {profile.label} | "
                    f"{', '.join(needs) or 'nothing'} | {refs} | {limit} | "
                    f"`{profile.acquisition_cost.value}` |"
                )
        else:
            add("None configured.")
        add("")

        if review:
            add("**Assessment**")
            add("")
            add("| Activity | Verdict |")
            add("|---|---|")
            from .registry.models import ASSESSED_ACTIVITIES

            for activity in ASSESSED_ACTIVITIES:
                add(
                    f"| {activity.replace('_', ' ')} | {_cell(review.assessment(activity).value)} |"
                )
            add("")

            if review.conditions:
                add("**Conditions**")
                add("")
                for condition in review.conditions:
                    add(f"- {condition}")
                add("")

            if review.review_notes:
                add("**Reviewer notes**")
                add("")
                add(f"{review.review_notes}")
                add("")

            if review.open_questions:
                add("**Open questions**")
                add("")
                for question in review.open_questions:
                    add(f"- {question}")
                add("")

            add(f"**Official evidence ({len(review.evidence)})**")
            add("")
            if review.evidence:
                for item in review.evidence:
                    add(
                        f"- [{item.document_title}]({item.document_url}) — "
                        f"`{item.document_type.value}`, retrieved "
                        f"{item.retrieved_at.date().isoformat()}"
                        + (f", section: {item.section_reference}" if item.section_reference else "")
                    )
                    add(f"  - {item.summarized_finding}")
            else:
                add("None. This assessment rests on no retrieved document, which is why it")
                add("cannot approve anything.")
            add("")

        if result.blocking_reasons:
            add("**Blocked by**")
            add("")
            for reason in result.blocking_reasons:
                add(f"- {reason}")
            add("")

        add("---")
        add("")

    return "\n".join(lines).rstrip("\n") + "\n"
