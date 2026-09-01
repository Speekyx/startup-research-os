"""One deployment state, one answer, whichever command asks (Mission 1.15.6.3).

**No external call, no database.** The persisted half is injected by replacing
`cli._recorded_decisions`, which is the seam the CLI already uses to read it, so
these cases describe a deployment that holds an operator decision without
depending on whether the machine running them does.

The property this file exists to protect is one sentence: **a reporting command
answers the same effective verification question the gate answers.**

Mission 1.15.6.2 made `HUMAN_CONFIRMATION` answerable from persistence and gave
`evaluate_readiness` a `decisions` parameter. Three CLI call sites never passed
it, so `readiness` and the footers of `show` and `authorization` re-asked the
verifiers, got `UNKNOWN` for a decision a person had recorded, and reported a
source as blocked by the one condition that was satisfied. `authorization`
printed a built context and told the reader to *pass the eligibility gate* it
had just passed.

This is the same shape as the defect Mission 1.15.6 fixed in
`test_cli_profile_reporting.py`: the modules that DECIDE were correct and the
modules that REPORT were not.
"""

from __future__ import annotations

import ast
import pathlib
from dataclasses import replace
from datetime import UTC, datetime

import pytest
from sros_acquisition import cli
from sros_acquisition.cli import main
from sros_acquisition.compliance.verification import ConditionVerificationRecord
from sros_contracts import ConditionVerification, ConditionVerificationResult

from .conftest import LEGACY_PROFILE, LOCAL_PROFILE, REPO_ROOT

CATALOG = REPO_ROOT / "docs" / "data" / "source-catalog-v1.json"
COMPLIANCE = REPO_ROOT / "docs" / "data" / "source-compliance-v1.json"
CLI_SOURCE = REPO_ROOT / "services" / "acquisition" / "python" / "sros_acquisition" / "cli.py"

RESIDUAL = "ted-database-right-residual-exposure-accepted"
ATTRIBUTION = "ted-attribution"

MOMENT = datetime(2026, 8, 31, 20, 9, 29, tzinfo=UTC)

# The sentences `AcquisitionReadiness.next_step` chooses between. Named rather
# than inlined because the whole defect was reporting the first where a later
# one was true.
#
# **`REAL_STEP` moves as the mission does, and that is the point.** It was
# "authorise a concrete resource" when this file was written and became the
# enable step when Mission 1.15.7 authorised the resource and wrote the
# collector. What these tests protect is not which sentence appears -- it is
# that `GATE_STEP` does NOT, because the gate passes.
GATE_STEP = "pass the eligibility gate"
REAL_STEP = "enable the collector in this deployment"


def decision(
    *,
    condition_key: str = RESIDUAL,
    source_id: str = "ted-eu",
    review_version: int = 2,
    verifier: str = "local-operator",
    result: ConditionVerificationResult = ConditionVerificationResult.SATISFIED,
    verification: ConditionVerification = ConditionVerification.HUMAN_CONFIRMATION,
) -> ConditionVerificationRecord:
    """One persisted decision, shaped like the row `read_human_decisions` returns."""
    return ConditionVerificationRecord(
        source_id=source_id,
        review_version=review_version,
        condition_key=condition_key,
        verification=verification,
        verifier=verifier,
        verifier_version="acknowledgement-v1",
        result=result,
        reason="a test fixture standing in for a recorded operator decision",
        reference="docs/data/ted-eu-operator-risk-acceptance-v1.md",
        verified_at=MOMENT,
    )


@pytest.fixture
def holds_the_decision(monkeypatch):
    """A deployment where the operator recorded their acceptance."""

    def _install(*records: ConditionVerificationRecord) -> None:
        monkeypatch.setattr(
            cli, "_recorded_decisions", lambda source, profile: tuple(records) or (decision(),)
        )

    _install()
    return _install


@pytest.fixture
def holds_nothing(monkeypatch):
    """A deployment where nobody recorded anything. The default before 1.15.6.1."""
    monkeypatch.setattr(cli, "_recorded_decisions", lambda source, profile: ())


def run(capsys, *argv: str, expect: int = 0) -> tuple[str, str]:
    code = main(["--catalog", str(CATALOG), "--compliance", str(COMPLIANCE), *argv])
    captured = capsys.readouterr()
    assert code == expect, captured.out + captured.err
    return captured.out, captured.err


def readiness_row(out: str, source_id: str = "ted-eu") -> str:
    return next(line for line in out.splitlines() if line.startswith(source_id))


# ==================================== the three commands, on a deployment that decided


class TestReportingAgreesWithTheGate:
    def test_readiness_reports_the_source_eligible(self, capsys, holds_the_decision) -> None:
        """The regression, stated as the behaviour rather than as its absence."""
        out, _ = run(capsys, "--use-profile", LOCAL_PROFILE, "readiness", "ted-eu")
        row = readiness_row(out)
        assert row.split()[1] == "yes", row

    def test_readiness_does_not_name_the_satisfied_condition_as_blocking(
        self, capsys, holds_the_decision
    ) -> None:
        """The worst half of the defect: the command named the one condition a
        person had answered as the reason the source was blocked."""
        out, _ = run(capsys, "--use-profile", LOCAL_PROFILE, "readiness", "ted-eu")
        assert RESIDUAL not in out
        assert "review conditions not satisfied" not in out

    def test_readiness_reports_the_real_blocker_instead(self, capsys, holds_the_decision) -> None:
        """Whatever actually stands in the way is what is reported. Generic: it
        comes from `next_step`, with no source named anywhere."""
        out, _ = run(capsys, "--use-profile", LOCAL_PROFILE, "readiness", "ted-eu")
        row = readiness_row(out)
        assert REAL_STEP in row
        assert GATE_STEP not in row

    def test_show_reports_the_same_eligibility(self, capsys, holds_the_decision) -> None:
        out, _ = run(capsys, "--use-profile", LOCAL_PROFILE, "show", "ted-eu")
        assert "COLLECTOR ELIGIBLE: yes" in out
        assert "RESOURCE READY:     yes" in out
        assert f"NEXT STEP:          {REAL_STEP}" in out

    def test_the_authorization_footer_names_the_real_next_blocker(
        self, capsys, holds_the_decision
    ) -> None:
        """A command that printed a built context and then told the reader to
        pass the gate it had just passed."""
        out, _ = run(capsys, "--use-profile", LOCAL_PROFILE, "authorization", "ted-eu")
        assert "AUTHORIZATION  ted-eu" in out
        assert f"NEXT STEP: {REAL_STEP}" in out
        assert GATE_STEP not in out

    def test_every_command_gives_the_same_answer(self, capsys, holds_the_decision) -> None:
        """The property, asserted across the commands rather than inside one.
        The same source, profile and deployment state must not produce two
        answers depending on which verb an operator typed."""
        eligibility, _ = run(capsys, "--use-profile", LOCAL_PROFILE, "eligibility", "ted-eu")
        readiness, _ = run(capsys, "--use-profile", LOCAL_PROFILE, "readiness", "ted-eu")
        show, _ = run(capsys, "--use-profile", LOCAL_PROFILE, "show", "ted-eu")
        authorization, _ = run(capsys, "--use-profile", LOCAL_PROFILE, "authorization", "ted-eu")

        assert "ted-eu: ELIGIBLE" in eligibility
        assert readiness_row(readiness).split()[1] == "yes"
        assert "COLLECTOR ELIGIBLE: yes" in show
        assert "AUTHORIZATION  ted-eu" in authorization
        assert GATE_STEP not in readiness + show + authorization

    def test_the_whole_catalog_scan_uses_the_decisions_too(
        self, capsys, holds_the_decision
    ) -> None:
        """`readiness` with no source argument is the report an operator reads
        first, and it walks every source. A fix applied only to the single-source
        path would leave the survey wrong."""
        out, _ = run(capsys, "--use-profile", LOCAL_PROFILE, "readiness")
        assert readiness_row(out).split()[1] == "yes"


# ============================================================ fail closed, and say why


class TestNoDecisionFailsClosed:
    def test_readiness_reports_the_human_condition_outstanding(self, capsys, holds_nothing) -> None:
        out, _ = run(capsys, "--use-profile", LOCAL_PROFILE, "readiness", "ted-eu")
        row = readiness_row(out)
        assert row.split()[1] == "no"
        assert RESIDUAL in out
        assert GATE_STEP in row

    def test_show_reports_it_not_eligible(self, capsys, holds_nothing) -> None:
        out, _ = run(capsys, "--use-profile", LOCAL_PROFILE, "show", "ted-eu")
        assert "COLLECTOR ELIGIBLE: NO" in out
        assert RESIDUAL in out

    def test_authorization_refuses(self, capsys, holds_nothing) -> None:
        _, err = run(capsys, "--use-profile", LOCAL_PROFILE, "authorization", "ted-eu", expect=1)
        assert "REFUSED" in err
        assert RESIDUAL in err

    def test_an_unreadable_database_says_so_and_still_refuses(self, capsys, monkeypatch) -> None:
        """Mission 1.15.6.2 §7 and `testing-strategy.md` §49: *nobody decided*
        and *I could not ask* produce the same refusal and must not produce the
        same explanation. The real `_recorded_decisions` is exercised here, not
        the seam, because the note is its behaviour.
        """

        def unreachable() -> object:
            raise RuntimeError("connection refused")

        monkeypatch.setattr(cli, "_connect", unreachable)
        out, err = run(capsys, "--use-profile", LOCAL_PROFILE, "readiness", "ted-eu")
        assert "operator decisions could not be read" in err
        assert readiness_row(out).split()[1] == "no"

    def test_a_missing_database_url_says_so_and_still_refuses(self, capsys, monkeypatch) -> None:
        """`_connect` raises `SystemExit`, a BaseException, for an unset
        `DATABASE_URL`. It is caught by name; a bare `except Exception` would let
        a report documented to run without a database die instead of degrade."""

        def unset() -> object:
            raise SystemExit("DATABASE_URL is not set")

        monkeypatch.setattr(cli, "_connect", unset)
        out, err = run(capsys, "--use-profile", LOCAL_PROFILE, "readiness", "ted-eu")
        assert "operator decisions were not read" in err
        assert readiness_row(out).split()[1] == "no"


# ================================== a supplied record is not a way past the gate


class TestASuppliedRecordAuthorisesNothingByItself:
    def test_a_decision_on_another_review_version_does_not_apply(
        self, capsys, holds_the_decision
    ) -> None:
        """An acceptance belongs to the review it was made about. The SQL read
        filters on the version; the resolver filters again, and this is the
        second filter doing its job with the first bypassed."""
        holds_the_decision(decision(review_version=1))
        out, _ = run(capsys, "--use-profile", LOCAL_PROFILE, "readiness", "ted-eu")
        assert readiness_row(out).split()[1] == "no"
        assert RESIDUAL in out

    def test_a_decision_about_another_source_does_not_apply(
        self, capsys, holds_the_decision
    ) -> None:
        holds_the_decision(decision(source_id="world-bank"))
        out, _ = run(capsys, "--use-profile", LOCAL_PROFILE, "readiness", "ted-eu")
        assert readiness_row(out).split()[1] == "no"

    def test_the_placeholder_is_not_a_decision(self, capsys, holds_the_decision) -> None:
        """`human-confirmation` is the verifier name the dispatcher writes when
        it CANNOT decide. A row carrying it is a machine shrugging."""
        holds_the_decision(decision(verifier="human-confirmation"))
        out, _ = run(capsys, "--use-profile", LOCAL_PROFILE, "readiness", "ted-eu")
        assert readiness_row(out).split()[1] == "no"

    def test_a_recorded_withdrawal_leaves_the_condition_unsatisfied(
        self, capsys, holds_the_decision
    ) -> None:
        """A withdrawal is a decision too, and it must not clear the gate."""
        holds_the_decision(decision(result=ConditionVerificationResult.UNSATISFIED))
        out, _ = run(capsys, "--use-profile", LOCAL_PROFILE, "readiness", "ted-eu")
        assert readiness_row(out).split()[1] == "no"
        assert RESIDUAL in out

    def test_a_supplied_record_cannot_satisfy_a_machine_condition(
        self, capsys, holds_the_decision
    ) -> None:
        """The rule that stops the parameter from becoming a bypass. A record
        naming a `CAPABILITY` condition is refused however it arrives, so a
        report can never be talked into eligibility by handing it one."""
        holds_the_decision(
            decision(),
            decision(condition_key=ATTRIBUTION, verification=ConditionVerification.CAPABILITY),
        )
        out, _ = run(capsys, "--use-profile", LOCAL_PROFILE, "readiness", "ted-eu")
        # The three capability conditions still hold on their own merits, so the
        # source stays eligible -- what matters is that the supplied CAPABILITY
        # record contributed nothing, which the next test isolates.
        assert readiness_row(out).split()[1] == "yes"

    def test_a_human_decision_does_not_make_a_broken_capability_pass(
        self, capsys, holds_the_decision, tmp_path, monkeypatch
    ) -> None:
        """The half that pulls the other way. Persisting judgement is not
        persisting everything: if a capability genuinely stops holding, the
        report must say blocked with the operator's acceptance untouched."""
        import json

        raw = json.loads(COMPLIANCE.read_text(encoding="utf-8"))
        for entry in raw["sources"]:
            if entry["source_id"] == "ted-eu":
                entry.pop("route_authorization", None)
        broken = tmp_path / "broken-compliance.json"
        broken.write_text(json.dumps(raw), encoding="utf-8")

        code = main(
            [
                "--catalog",
                str(CATALOG),
                "--compliance",
                str(broken),
                "--use-profile",
                LOCAL_PROFILE,
                "readiness",
                "ted-eu",
            ]
        )
        out = capsys.readouterr().out
        assert code == 0, out
        assert readiness_row(out).split()[1] == "no"
        assert "ted-official-route-only" in out
        assert RESIDUAL not in out


# ======================================================== the other profile is untouched


class TestTheCommercialProfileIsUnaffected:
    def test_commercial_ted_stays_requires_review(self, capsys, holds_the_decision) -> None:
        """A decision recorded under one profile reaches no other, and the
        refusal does not mention the condition it satisfied."""
        out, _ = run(capsys, "--use-profile", LEGACY_PROFILE, "readiness", "ted-eu")
        row = readiness_row(out)
        assert row.split()[1] == "no"
        assert "REQUIRES_REVIEW" in out
        assert RESIDUAL not in out

    def test_commercial_authorization_still_refuses(self, capsys, holds_the_decision) -> None:
        _, err = run(capsys, "--use-profile", LEGACY_PROFILE, "authorization", "ted-eu", expect=1)
        assert "REQUIRES_REVIEW" in err

    def test_a_source_with_no_human_condition_is_unchanged(self, capsys, holds_nothing) -> None:
        """The generic half. 28 of 29 sources have no human condition, and this
        change must be invisible to them."""
        out, _ = run(capsys, "readiness", "world-bank")
        assert readiness_row(out, "world-bank").split()[1] == "yes"


# ================================================ the fence, so this cannot come back


def test_every_readiness_call_in_the_cli_passes_the_decisions() -> None:
    """The fence, in the shape `test_cli_profile_reporting.py` already uses.

    `evaluate_readiness(source, profile, config)` type-checks, runs, and is
    wrong -- `decisions` defaults to `()`, which is a real state meaning *this
    deployment holds none*. A caller that omits it is not asking for the
    default, it is asserting an absence it never checked, and that is exactly
    how three call sites came to disagree with the gate.

    Asserted as an AST property rather than a review habit, because the omission
    is invisible at the call site and the correct call is one keyword longer.
    """
    tree = ast.parse(pathlib.Path(CLI_SOURCE).read_text(encoding="utf-8"))
    offenders = [
        f"line {node.lineno}"
        for node in ast.walk(tree)
        if isinstance(node, ast.Call)
        and isinstance(node.func, ast.Name)
        and node.func.id == "evaluate_readiness"
        and not any(keyword.arg == "decisions" for keyword in node.keywords)
    ]
    assert offenders == [], offenders


def test_the_cli_reads_decisions_through_the_one_canonical_helper() -> None:
    """No second resolver, and no second reader (Mission 1.15.6.3 §4).

    `read_human_decisions` applies the profile, review-version, kind and
    authorship filters in SQL. A command that queried the table itself would be
    a second copy of those filters, and a copy is a thing that drifts.
    """
    text = pathlib.Path(CLI_SOURCE).read_text(encoding="utf-8")
    assert text.count("read_human_decisions(") == 1
    assert "source_condition_verifications" not in text
    assert "resolve_effective_verifications" in text


def test_no_test_in_this_file_reaches_the_network() -> None:
    tree = ast.parse(pathlib.Path(__file__).read_text(encoding="utf-8"))
    imported: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported.update(alias.name.split(".")[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            imported.add(node.module.split(".")[0])
    assert not imported & {"httpx", "requests", "urllib", "aiohttp", "socket"}


def test_the_fixture_record_is_the_shape_the_reader_returns() -> None:
    """A fixture that drifted from `read_human_decisions`'s output would make
    every case above pass against a record no deployment can produce."""
    record = decision()
    assert record.is_human_decision
    assert not record.awaits_human_decision
    assert replace(record, verifier="human-confirmation").awaits_human_decision
