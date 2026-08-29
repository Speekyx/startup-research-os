"""The synthetic sensitivity harness.

Mission 1.1 §31. Thirteen scenarios, each built to answer one question about
whether the mathematics behaves the way the specification says it should.

**Everything here is synthetic.** No platform was contacted, no registered
source id appears, and every provenance relationship is stated by the scenario
rather than inferred — semantic deduplication is `nlp`'s job and D-12 is open.
The scenarios exist to exercise the operators, not to describe any real market.

**The constants below are not tuned.** They were chosen to be legible — 0.8 for
strong, 0.5 for medium, 0.2 for weak — and then left alone. Adjusting them until
the report reads well would be fitting the illustration to the conclusion, which
is the one thing a sensitivity analysis must not do.

    python -m sros_evidence_aggregation.sensitivity
"""

from __future__ import annotations

from collections.abc import Callable, Sequence
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta

from sros_contracts import (
    AggregationProfileStatus,
    ClaimTemporality,
    EvidenceDirection,
    EvidenceIndependenceState,
    EvidenceObservationCategory,
)

from .engine import aggregate
from .items import EvidenceItem
from .profile import REFERENCE_PROFILE_V1, EvidenceAggregationProfile
from .result import EvidenceAggregationResult

__all__ = ["SCENARIOS", "Scenario", "run_scenario", "run_all", "render_markdown"]

# A fixed clock. A sensitivity report whose numbers move with the wall clock
# cannot be reviewed against its previous version.
NOW = datetime(2026, 8, 29, 12, 0, 0, tzinfo=UTC)

STRONG, MEDIUM, WEAK = 0.8, 0.5, 0.2

# `None` already means "use q" in the helper below, so a scenario needs a
# different way to say "this field is genuinely absent". Without the sentinel
# the missing-input scenario silently tested nothing -- which is exactly the
# failure it exists to detect.
ABSENT = object()

# A profile WITH a half-life, used only by the recency scenarios. Its 30-day
# value is a scenario input, not a project parameter: it is declared here, in a
# synthetic harness, and REFERENCE_PROFILE_V1 still ships with no half-life at
# all (§19).
TEMPORAL_SCENARIO_PROFILE = EvidenceAggregationProfile(
    profile_id="synthetic-temporal",
    version="0.0.0",
    status=AggregationProfileStatus.UNCALIBRATED,
    half_life_days={"synthetic-trend": 30.0},
    notes=(
        "Synthetic. Exists so the decay curve can be demonstrated. The 30-day half-life "
        "is an illustration chosen for arithmetic legibility and is NOT a project "
        "parameter, NOT calibrated, and must never be copied into a real profile."
    ),
)


def _item(
    evidence_id: str,
    *,
    q: float = MEDIUM,
    direction: EvidenceDirection = EvidenceDirection.SUPPORTS,
    state: EvidenceIndependenceState = EvidenceIndependenceState.KNOWN_INDEPENDENT,
    group: str | None = None,
    category: EvidenceObservationCategory = EvidenceObservationCategory.STATED_OPINION,
    family: str = "synthetic-family-a",
    reliability: float | None | object = None,
    observed_at: datetime | None = None,
) -> EvidenceItem:
    if reliability is ABSENT:
        resolved_reliability: float | None = None
    elif reliability is None:
        resolved_reliability = q
    else:
        resolved_reliability = float(reliability)  # type: ignore[arg-type]
    return EvidenceItem(
        evidence_id=evidence_id,
        direction=direction,
        relevance=q,
        directness=q,
        reliability=resolved_reliability,
        extraction_confidence=q,
        independence_state=state,
        independence_group_id=group,
        observation_category=category,
        source_id=f"synthetic-source-{evidence_id}",
        source_family=family,
        observed_at=observed_at,
    )


@dataclass(frozen=True)
class Scenario:
    """One question, and the evidence set that answers it."""

    key: str
    title: str
    question: str
    expectation: str
    build: Callable[[], Sequence[EvidenceItem]]
    temporality: ClaimTemporality = ClaimTemporality.EVERGREEN
    claim_feature: str | None = None
    profile: EvidenceAggregationProfile = REFERENCE_PROFILE_V1


def _one_strong_group() -> Sequence[EvidenceItem]:
    return [_item("strong-1", q=STRONG)]


def _ten_duplicates() -> Sequence[EvidenceItem]:
    # One origin, ten records. The strongest is 0.8, exactly the single-group
    # case above, which is the point being demonstrated.
    return [
        _item(
            f"dup-{i}",
            q=STRONG if i == 0 else MEDIUM,
            state=EvidenceIndependenceState.KNOWN_DEPENDENT,
            group="origin-announcement",
        )
        for i in range(10)
    ]


def _three_independent_medium() -> Sequence[EvidenceItem]:
    return [
        _item(f"ind-{i}", q=MEDIUM, family=f"synthetic-family-{chr(ord('a') + i)}")
        for i in range(3)
    ]


def _support_and_contradiction() -> Sequence[EvidenceItem]:
    return [
        _item("sup-1", q=STRONG),
        _item("sup-2", q=STRONG, family="synthetic-family-b"),
        _item("con-1", q=STRONG, direction=EvidenceDirection.CONTRADICTS),
        _item(
            "con-2", q=STRONG, direction=EvidenceDirection.CONTRADICTS, family="synthetic-family-b"
        ),
    ]


def _stale_evidence() -> Sequence[EvidenceItem]:
    # Two half-lives old under the synthetic 30-day profile: freshness 0.25,
    # which then becomes the limiting component.
    return [_item("stale-1", q=STRONG, observed_at=NOW - timedelta(days=60))]


def _fresh_evidence() -> Sequence[EvidenceItem]:
    return [_item("fresh-1", q=STRONG, observed_at=NOW - timedelta(days=1))]


def _evergreen_evidence() -> Sequence[EvidenceItem]:
    return [_item("evergreen-1", q=STRONG, observed_at=NOW - timedelta(days=3650))]


def _unknown_independence() -> Sequence[EvidenceItem]:
    return [_item(f"unk-{i}", q=MEDIUM, state=EvidenceIndependenceState.UNKNOWN) for i in range(10)]


def _missing_reliability() -> Sequence[EvidenceItem]:
    return [
        _item("has-reliability", q=MEDIUM),
        _item("no-reliability", q=MEDIUM, reliability=ABSENT),
    ]


def _many_weak_groups() -> Sequence[EvidenceItem]:
    return [_item(f"weak-{i}", q=WEAK, family=f"synthetic-family-{i % 4}") for i in range(12)]


def _market_evidence() -> Sequence[EvidenceItem]:
    return [
        _item(
            "market-1",
            q=MEDIUM,
            category=EvidenceObservationCategory.MARKET_ACTIVITY,
            family="synthetic-family-market",
        )
    ]


def _loud_opinion() -> Sequence[EvidenceItem]:
    return [_item(f"opinion-{i}", q=STRONG, family=f"synthetic-family-{i % 5}") for i in range(20)]


SCENARIOS: tuple[Scenario, ...] = (
    Scenario(
        "one-strong-group",
        "One strong independent group",
        "Does a single strong observation carry its own weight?",
        "support_strength equals the item strength. No dilution by averaging.",
        _one_strong_group,
    ),
    Scenario(
        "ten-duplicates",
        "Ten records, one origin",
        "Can duplicates outvote an original?",
        "Identical to the single-group case. Nine records collapse and add nothing.",
        _ten_duplicates,
    ),
    Scenario(
        "three-independent-medium",
        "Three independent medium groups",
        "Does genuinely independent evidence accumulate?",
        "support_strength exceeds any single group but stays below 1, with falling marginal gain.",
        _three_independent_medium,
    ),
    Scenario(
        "support-and-contradiction",
        "Strong support and strong contradiction",
        "Does conflict stay visible instead of netting to nothing?",
        "conflict_mass dominates. Evidence Score is low, and a low score here means "
        "contested rather than unsupported -- the diagnostics are what tell them apart.",
        _support_and_contradiction,
    ),
    Scenario(
        "stale-evidence",
        "Stale evidence, temporally sensitive claim",
        "Does age reduce contribution?",
        "Two half-lives gives freshness 0.25, which becomes the limiting component.",
        _stale_evidence,
        temporality=ClaimTemporality.TEMPORALLY_SENSITIVE,
        claim_feature="synthetic-trend",
        profile=TEMPORAL_SCENARIO_PROFILE,
    ),
    Scenario(
        "fresh-evidence",
        "Fresh evidence, same claim",
        "Is the same observation stronger when newer?",
        "Strictly stronger than the stale case. Nothing else differs.",
        _fresh_evidence,
        temporality=ClaimTemporality.TEMPORALLY_SENSITIVE,
        claim_feature="synthetic-trend",
        profile=TEMPORAL_SCENARIO_PROFILE,
    ),
    Scenario(
        "evergreen-evidence",
        "Ten-year-old evergreen evidence",
        "Does an evergreen claim decay?",
        "freshness is 1.0. Age is irrelevant to a claim that does not decay.",
        _evergreen_evidence,
    ),
    Scenario(
        "missing-temporal-parameter",
        "Temporally sensitive claim, no authorised half-life",
        "What happens when a required parameter was never authorised?",
        "MISSING_TEMPORAL_PARAMETER, UNAVAILABLE, and no score. Not a guessed decay.",
        _fresh_evidence,
        temporality=ClaimTemporality.TEMPORALLY_SENSITIVE,
        claim_feature="unauthorised-feature",
    ),
    Scenario(
        "unknown-independence",
        "Ten records of unknown provenance",
        "Does unestablished provenance accumulate as independent evidence?",
        "One group. Strength equals the strongest single record, and the other nine "
        "raise observed volume only.",
        _unknown_independence,
    ),
    Scenario(
        "missing-reliability",
        "One record missing reliability",
        "Is a missing input given a default?",
        "The record is NON-SCORABLE and named in missing_requirements. Status PARTIAL.",
        _missing_reliability,
    ),
    Scenario(
        "many-weak-groups",
        "Twelve weak independent groups",
        "Can a large volume of weak evidence saturate towards certainty?",
        "support_strength rises but stays well below 1, with clearly diminishing returns.",
        _many_weak_groups,
    ),
    Scenario(
        "market-evidence-vs-volume",
        "One market-activity record",
        "Does the KIND of observation beat the QUANTITY of opinion?",
        "EvidenceLevel 4 from one record, where twenty strong opinions reach 3.",
        _market_evidence,
    ),
    Scenario(
        "loud-opinion",
        "Twenty strong opinions across five families",
        "Can volume of opinion reach Market Evidence?",
        "EvidenceLevel 3, never 4. No amount of stated opinion becomes market activity.",
        _loud_opinion,
    ),
)


def run_scenario(scenario: Scenario) -> EvidenceAggregationResult:
    return aggregate(
        f"synthetic-{scenario.key}",
        list(scenario.build()),
        scenario.profile,
        temporality=scenario.temporality,
        claim_feature=scenario.claim_feature,
        now=NOW,
        allow_uncalibrated=True,
    )


def run_all() -> list[tuple[Scenario, EvidenceAggregationResult]]:
    return [(scenario, run_scenario(scenario)) for scenario in SCENARIOS]


def _fmt(value: float | None, places: int = 4) -> str:
    return "—" if value is None else f"{value:.{places}f}"


def _findings_section(by_key: dict[str, EvidenceAggregationResult]) -> list[str]:
    """The interpretation, with its numbers read back out of the run.

    Written to record what the operators actually do, including where that is
    uncomfortable. §31 forbids tuning constants until the report reads well, and
    the corollary is that an inconvenient result gets written down rather than
    adjusted away.
    """
    single = by_key["one-strong-group"]
    duplicated = by_key["ten-duplicates"]
    unknown = by_key["unknown-independence"]
    loud = by_key["loud-opinion"]
    weak = by_key["many-weak-groups"]
    market = by_key["market-evidence-vs-volume"]
    conflict = by_key["support-and-contradiction"]

    single_score = single.evidence_score or 0.0
    duplicated_score = duplicated.evidence_score or 0.0
    loud_score = loud.evidence_score or 0.0
    weak_score = weak.evidence_score or 0.0

    return [
        "",
        "---",
        "",
        "## Findings",
        "",
        "### Behaviour that matches the specification",
        "",
        f"**Duplicates cannot inflate strength.** Ten records from one origin produce "
        f"{duplicated_score:.2f}, identical to the single record at {single_score:.2f}. "
        "Nine collapse and add nothing. This is the property the independence model "
        "exists for, and it holds exactly rather than approximately.",
        "",
        f"**Unknown provenance is conservative.** Ten records of unestablished origin "
        f"produce {unknown.evidence_score:.2f} from "
        f"{unknown.support_group_count} group, not ten. They raise observed volume "
        "and nothing else.",
        "",
        "**Contradiction stays visible.** Strong evidence both ways gives "
        f"conflict_mass {conflict.masses.conflict_mass:.4f} with a score of "
        f"{conflict.evidence_score:.2f}. The low score means *contested*, and the only "
        "thing that distinguishes it from *unsupported* is the diagnostics beside it. "
        "A score published alone would be actively misleading here.",
        "",
        f"**Category beats quantity.** One market-activity record reaches EvidenceLevel "
        f"{market.level.level}; twenty strong opinions across five families reach "
        f"{loud.level.level} and cannot go higher. No accumulation of opinion becomes "
        "market evidence.",
        "",
        "**Missing inputs fail closed.** A record missing reliability is NON-SCORABLE "
        "and named, not defaulted. A temporally sensitive claim with no authorised "
        "half-life yields no score at all rather than a guessed decay.",
        "",
        "### Finding S-1 — the score saturates towards 100, and that is a problem",
        "",
        f"Twenty independent strong groups produce a score of {loud_score:.2f}, which "
        f"presents as **{loud.presented_evidence_score}**. Twelve *weak* independent "
        f"groups produce {weak_score:.2f}.",
        "",
        "The operator is behaving exactly as defined — `1 - Π(1-g)` converges quickly "
        "once groups accumulate — and the arithmetic is not in question. The problem is "
        "how the output reads. A displayed `100` is indistinguishable from certainty, "
        "and no evidence set justifies certainty.",
        "",
        "Two things limit the damage today, and neither is a fix. EvidenceLevel does not "
        "move with the score, so the loud-opinion case is still Level 3 and visibly not "
        "market evidence. And `uncertainty_mass` goes to zero rather than pretending "
        "otherwise, so a reader who looks at the decomposition sees what happened.",
        "",
        "**No damping constant was added.** Introducing one would mean choosing its "
        "value here, in a synthetic harness, with no data — which is the exact failure "
        "D-03 was raised to prevent, committed in the course of resolving it. The "
        "honest options are a calibrated correction or a presentation cap, and both need "
        "the labelled data the calibration plan describes. This is recorded as the "
        "**first-priority calibration target**, not as a defect to be papered over "
        "before anyone notices it.",
        "",
        "### Finding S-2 — group count dominates group quality",
        "",
        f"Twelve weak groups ({weak_score:.2f}) outscore one strong group "
        f"({single_score:.2f}). That follows from saturation and is defensible: twelve "
        "genuinely independent weak observations *are* more than one strong one. But it "
        "puts the entire weight of the model on the independence judgement, because "
        "twelve records wrongly labelled independent produce the same number as twelve "
        "real ones.",
        "",
        "The mitigation is the conservative unknown-provenance rule, which collapses "
        "unlabelled records rather than trusting them. The residual risk is *incorrectly "
        "labelled* independence, which no arithmetic here can detect — it is a data "
        "quality problem for `nlp` deduplication (D-12), and worth stating plainly "
        "rather than leaving implicit.",
        "",
        "### What this analysis does not establish",
        "",
        "That the model is *correct*. Every scenario here checks whether the "
        "implementation does what the specification says, and all of them pass. None of "
        "them checks whether the specification predicts anything about real markets, "
        "because that requires labelled outcomes and none exist. See "
        "[`evidence-aggregation-calibration-plan-v1.md`]"
        "(evidence-aggregation-calibration-plan-v1.md).",
    ]


def render_markdown() -> str:
    """The report body. Generated, so it cannot drift from the implementation."""
    results = run_all()

    lines = [
        "# Evidence Aggregation V1 — sensitivity analysis",
        "",
        "**Status:** Generated. Do not edit by hand.",
        "**Generated by:** `python -m sros_evidence_aggregation.sensitivity`",
        f"**Algorithm version:** {results[0][1].algorithm_version}",
        "**Governed by:** [`evidence-aggregation-framework-v1.md`]"
        "(evidence-aggregation-framework-v1.md)",
        "",
        "> **Every scenario is synthetic.** No platform was contacted, no registered",
        "> source appears, and every provenance relationship is stated by the scenario",
        "> rather than detected — semantic deduplication belongs to `nlp` and D-12 is",
        "> open. These cases exercise the operators; they describe no real market.",
        "",
        "> **The parameters were not tuned.** Item strengths are 0.8 / 0.5 / 0.2, chosen",
        "> to be legible and then left alone. Tuning them until the table looked",
        "> convincing would be fitting the illustration to the conclusion.",
        "",
        "---",
        "",
        "## Summary",
        "",
        "| Scenario | s | c | supported | conflict | uncertainty | Score | Level | Status |",
        "|---|---|---|---|---|---|---|---|---|",
    ]

    for scenario, result in results:
        masses = result.masses
        score = result.evidence_score
        lines.append(
            f"| `{scenario.key}` | {_fmt(masses.support_strength)} | "
            f"{_fmt(masses.contradiction_strength)} | {_fmt(masses.supported_mass)} | "
            f"{_fmt(masses.conflict_mass)} | {_fmt(masses.uncertainty_mass)} | "
            f"{'—' if score is None else f'{score:.2f}'} | {result.level.level} | "
            f"`{result.status.value}` |"
        )

    lines.extend(_findings_section({s.key: r for s, r in results}))
    lines.extend(["", "---", "", "## Scenario detail", ""])

    for scenario, result in results:
        lines.extend(
            [
                f"### {scenario.title} — `{scenario.key}`",
                "",
                f"**Question.** {scenario.question}",
                "",
                f"**Expected behaviour.** {scenario.expectation}",
                "",
                f"Claim temporality: `{scenario.temporality.value}` · profile "
                f"`{scenario.profile.profile_id}` v{scenario.profile.version} "
                f"[{scenario.profile.status.value}]",
                "",
                "```text",
                result.explain(),
                "```",
                "",
            ]
        )

    return "\n".join(lines).rstrip("\n") + "\n"


DEFAULT_REPORT_PATH = "docs/domain/evidence-aggregation-sensitivity-v1.md"


def main(argv: list[str] | None = None) -> int:  # pragma: no cover - thin CLI
    """`--write` regenerates the report, `--check` fails if it has drifted.

    The report is generated from the implementation, so it cannot describe
    behaviour the code does not have. `--check` runs in CI for the reason
    ADR-009 gives about contracts: two hand-maintained copies of one fact drift,
    and the drift is found by whoever trusted the wrong one.
    """
    import argparse
    import pathlib

    parser = argparse.ArgumentParser(prog="sros-sensitivity")
    parser.add_argument("--write", action="store_true", help="write the report to disk")
    parser.add_argument("--check", action="store_true", help="fail if the report has drifted")
    parser.add_argument("--path", default=DEFAULT_REPORT_PATH)
    args = parser.parse_args(argv)

    rendered = render_markdown()
    path = pathlib.Path(args.path)

    if args.check:
        if not path.exists():
            print(f"missing  {path}", flush=True)
            return 1
        if path.read_text(encoding="utf-8") != rendered:
            print(
                f"stale    {path} does not match the implementation. Regenerate with --write",
                flush=True,
            )
            return 1
        print(f"ok       {path} matches the implementation")
        return 0

    if args.write:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(rendered, encoding="utf-8", newline=chr(10))
        print(f"wrote    {path}")
        return 0

    print(rendered)
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
