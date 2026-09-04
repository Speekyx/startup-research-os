"""A report answers about the profile it was asked about (Mission 1.15.6 follow-up).

**No external call, no database.** These exercise the reporting commands against
the real catalog and the real compliance configuration, which are the artefacts
under review.

The property this file exists to protect is one sentence: **every reporting
command reads the review for the profile the operator named, and says which
profile that was.**

Four commands read `source.review` -- the LEGACY profile's current review -- while
`--use-profile` selected a different one for the gate result printed beside it.
That was invisible while every source had exactly one review, and `ted-eu` is the
first that does not. The worst of the four returned

    ted-eu: the current review declares no condition

for a review carrying four, because TED's legacy review declares none and its
local review declares four. A silent false negative, in the command
`source-review-guide.md` §9 tells a reviewer to run, for the one source whose
conditions anybody needed to read.
"""

# Mission 1.17 reviewed world-bank, gdelt, eurostat, fred and openalex under
# `local-private-research-v1`, so world-bank stopped being an example of a source
# unreviewed under that profile. These tests now use `reddit`, which genuinely
# has no local review and is one of 23 that do not.
#
# The assertions themselves are UNCHANGED. What moved is the fixture, because
# what they check -- that an unreviewed profile reports an ABSENCE rather than
# an emptiness or a fallback -- is exactly as important as it was.

from __future__ import annotations

import pytest
from sros_acquisition.cli import main

from .conftest import LEGACY_PROFILE, LOCAL_PROFILE, REPO_ROOT, current_review_version

CATALOG = REPO_ROOT / "docs" / "data" / "source-catalog-v1.json"
COMPLIANCE = REPO_ROOT / "docs" / "data" / "source-compliance-v1.json"

RESIDUAL = "ted-database-right-residual-exposure-accepted"
ROUTE_ONLY = "ted-official-route-only"


def run(capsys, *argv: str) -> str:
    """One command, its stdout, and a non-zero exit reported as a failure."""
    code = main(["--catalog", str(CATALOG), "--compliance", str(COMPLIANCE), *argv])
    out = capsys.readouterr().out
    assert code == 0, out
    return out


# ======================================================= conditions, the bad one


class TestConditionsReadsTheRequestedProfile:
    def test_the_local_profile_reports_its_four_conditions(self, capsys) -> None:
        """The regression, stated as the behaviour rather than as its absence."""
        out = run(capsys, "--use-profile", LOCAL_PROFILE, "conditions", "ted-eu")
        assert "declares no condition" not in out
        assert "4 condition(s)" in out
        for key in ("ted-attribution", ROUTE_ONLY, "ted-personal-data-minimisation", RESIDUAL):
            assert key in out, key

    def test_it_names_the_profile_it_answered_about(self, capsys) -> None:
        """§8 of `use-profile-aware-source-policy-v1.md`: never a naked verdict.
        A condition list with no subject invites the reader to supply one."""
        out = run(capsys, "--use-profile", LOCAL_PROFILE, "conditions", "ted-eu")
        assert LOCAL_PROFILE in out

    def test_the_legacy_profile_still_reports_no_condition_for_ted(self, capsys) -> None:
        """The other half, and the reason the defect survived: under the DEFAULT
        profile the old output was correct. TED's legacy review really does
        declare none, so the command was right for most sources and silently wrong
        for the 29th."""
        out = run(capsys, "conditions", "ted-eu")
        assert "declares no condition" in out
        assert LEGACY_PROFILE in out

    def test_an_unreviewed_profile_reports_an_absence_not_an_emptiness(self, capsys) -> None:
        """A source with no review under a profile must not read as a source
        whose review imposed nothing. Absence is a refusal (§4)."""
        out = run(capsys, "--use-profile", LOCAL_PROFILE, "conditions", "reddit")
        assert "no policy review exists under" in out
        assert "never a reason to consult another profile" in out

    def test_the_legacy_default_is_unchanged_for_every_other_source(self, capsys) -> None:
        out = run(capsys, "conditions", "world-bank")
        assert "condition(s)" in out
        assert "no policy review exists" not in out


# ================================================================== list


class TestListReportsOneProfilePerRow:
    def test_the_state_and_the_gate_answer_the_same_question(self, capsys) -> None:
        """The STATE column read the legacy review while ELIGIBLE beside it was
        per-profile, so under a second profile one row carried two answers to
        two different questions with nothing saying so.

        **The ELIGIBLE value is deployment state and is deliberately not
        asserted** (`testing-strategy.md` §49). TED is eligible where an
        operator recorded their acceptance and not where they did not, and this
        test is about which REVIEW the state column reports -- a repository
        fact, true on every machine.
        """
        out = run(capsys, "--use-profile", LOCAL_PROFILE, "list")
        ted = next(line for line in out.splitlines() if line.startswith("ted-eu"))
        assert "APPROVED_WITH_CONDITIONS" in ted
        assert ted.rstrip().rsplit(maxsplit=1)[-1] in {"yes", "no"}

    def test_the_legacy_view_still_shows_the_legacy_verdict(self, capsys) -> None:
        out = run(capsys, "list")
        ted = next(line for line in out.splitlines() if line.startswith("ted-eu"))
        assert "REQUIRES_REVIEW" in ted

    def test_a_source_unreviewed_under_the_profile_says_so(self, capsys) -> None:
        out = run(capsys, "--use-profile", LOCAL_PROFILE, "list")
        unreviewed = next(line for line in out.splitlines() if line.startswith("reddit"))
        assert "NO REVIEW" in unreviewed
        assert "have NO review under this profile" in out

    def test_it_names_the_profile(self, capsys) -> None:
        assert LOCAL_PROFILE in run(capsys, "--use-profile", LOCAL_PROFILE, "list")
        assert LEGACY_PROFILE in run(capsys, "list")


# ================================================================== show


class TestShowReportsTheRequestedProfile:
    def test_it_shows_the_requested_review_not_the_legacy_one(self, capsys) -> None:
        out = run(capsys, "--use-profile", LOCAL_PROFILE, "show", "ted-eu")
        # The property is that `show` reports the LOCAL review rather than the
        # legacy one, not that the local line is frozen at v2. It was pinned to
        # "v2 ... by mission-1.15.6" and Mission 1.45 appended v3.
        version = current_review_version()
        assert f"POLICY REVIEW v{version}  APPROVED_WITH_CONDITIONS" in out
        # And the legacy review is a different version in a different state, so
        # naming it would be the failure this test exists to catch.
        legacy_version = current_review_version(use_profile=LEGACY_PROFILE)
        assert f"POLICY REVIEW v{legacy_version}  REQUIRES_REVIEW" not in out

    def test_it_lists_every_profile_the_source_is_reviewed_under(self, capsys) -> None:
        """A standing is a table. A reader shown one profile could not tell
        whether the others exist, which is how a local approval gets read as
        the whole answer."""
        out = run(capsys, "--use-profile", LOCAL_PROFILE, "show", "ted-eu")
        assert "STANDING" in out
        assert "REQUIRES_REVIEW" in out
        assert "APPROVED_WITH_CONDITIONS" in out

    def test_the_scope_is_the_profile_not_the_inherited_prose(self, capsys) -> None:
        """The line that claimed the opposite of what it labelled. Every review
        inherits the catalog's `assessed_use_case` sentence -- "a COMMERCIAL
        multi-tenant SaaS", unchanged since Mission 1.0 -- so printing it as the
        scope of a LOCAL review asserted the one thing that review is not."""
        out = run(capsys, "--use-profile", LOCAL_PROFILE, "show", "ted-eu")
        scope = next(line for line in out.splitlines() if line.strip().startswith("scope"))
        assert LOCAL_PROFILE in scope
        assert "COMMERCIAL" not in scope
        # The prose survives, labelled as what it is rather than deleted.
        assert "inherited" in out
        assert "the profile above is the identity" in out.lower()

    def test_an_unreviewed_profile_refuses_rather_than_falling_back(self, capsys) -> None:
        out = run(capsys, "--use-profile", LOCAL_PROFILE, "show", "reddit")
        assert "NO POLICY REVIEW UNDER" in out
        assert "PER-ACTIVITY ASSESSMENT" not in out.upper()


# ================================================================== stale


class TestStaleScansTheRequestedProfile:
    def test_it_reports_no_stalled_review_under_the_local_profile(self, capsys) -> None:
        out = run(capsys, "--use-profile", LOCAL_PROFILE, "stale")
        assert "STALE REVIEWS (0)" in out
        assert "AWAITING REVIEW (0)" in out

    def test_unreviewed_is_counted_apart_from_awaiting_review(self, capsys) -> None:
        """A source nobody assessed for this use is not a review that stalled.
        Merging the two would put every unreviewed source into a queue under any profile but
        the legacy one, which is noise dressed as work."""
        out = run(capsys, "--use-profile", LOCAL_PROFILE, "stale")
        assert "NO REVIEW UNDER THIS PROFILE (21)" in out
        assert "Not a stalled review" in out

    def test_the_legacy_view_still_finds_the_sources_awaiting_review(self, capsys) -> None:
        out = run(capsys, "stale")
        assert "AWAITING REVIEW (" in out
        assert "ted-eu" in out
        assert "NO REVIEW UNDER THIS PROFILE" not in out


# ============================================ the accessor that caused it


def test_no_reporting_command_reads_the_legacy_scoped_accessor() -> None:
    """The fence, in the shape `test_use_profile_policy.py` already uses for the
    three gate modules.

    `source.review` is the LEGACY profile's review and reads more naturally than
    `source.review_for(profile)` -- which is precisely how this mistake was
    made, four times, by people writing what sounded right. The gate modules
    have had an AST fence since Mission 1.15.5; the reporting layer did not, and
    that is where the defect lived.

    `_profile_review` is the one sanctioned reader, so it is exempt by name.
    """
    import ast
    import pathlib

    cli = pathlib.Path(
        REPO_ROOT / "services" / "acquisition" / "python" / "sros_acquisition" / "cli.py"
    )
    tree = ast.parse(cli.read_text(encoding="utf-8"))

    offenders: list[str] = []
    for node in ast.walk(tree):
        if not isinstance(node, ast.FunctionDef):
            continue
        if node.name == "_profile_review":
            continue
        for inner in ast.walk(node):
            if (
                isinstance(inner, ast.Attribute)
                and inner.attr == "review"
                and isinstance(inner.value, ast.Name)
                and inner.value.id in {"source", "s"}
            ):
                offenders.append(f"{node.name}:{inner.lineno}")
    assert offenders == [], offenders


def test_no_test_in_this_file_reaches_the_network() -> None:
    import ast
    import pathlib

    tree = ast.parse(pathlib.Path(__file__).read_text(encoding="utf-8"))
    imported: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported.update(alias.name.split(".")[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            imported.add(node.module.split(".")[0])
    assert not imported & {"httpx", "requests", "urllib", "aiohttp", "socket"}


@pytest.mark.parametrize("command", ["list", "eligibility", "readiness", "stale"])
def test_every_broad_report_names_its_profile(capsys, command: str) -> None:
    """One assertion across the reports that scan the whole catalog. A number
    like "3 collector-eligible" means nothing without the profile it counted
    under, and it is the number most likely to be quoted elsewhere."""
    assert LOCAL_PROFILE in run(capsys, "--use-profile", LOCAL_PROFILE, command)
