"""Mission 1.84.17. Gate v1.3.0 against gate v1.4.0 on the same arguments, and what may differ.

Gate v1.4.0 is gate v1.3.0 with its structural check read against output schema v1.2.0 instead of
v1.1.0, and the two schemas differ in one leaf: the reasoning summary's maxLength. So the only
difference two verdicts on the same arguments may show is the one that leaf explains:

* COMMON: a summary no longer than the v1.1.0 bound, or not a string. Everything is equal, the
  structural reasons included once their schema prefix is set aside;
* BAND: a summary longer than the v1.1.0 bound and no longer than the v1.2.0 bound. v1.3.0's summary
  maxLength reason is absent from v1.4.0, and nothing else moves;
* ABOVE: a summary longer than the v1.2.0 bound. That reason names the v1.2.0 bound instead, in the
  same place, and nothing else moves.

Anything else is a divergence. The semantic half (every reason that is not a structural reason, the
audit and the notes) must be equal in all three domains. Both bounds are read from the schemas, so
this module carries no length of its own.

The second half is a pytest plugin. With `-p second_opportunity_gate_differential`, gate v1.3.0's own
frozen test file is replayed with every reference to the v1.3.0 evaluator replaced by a spy that runs
both gates on each call, classifies the pair and hands back v1.3.0's verdict, so every v1.3.0 test
still asserts what it asserted. The file is not edited: it is the v1.3.0 matrix, run as it stands.
"""

from __future__ import annotations

import functools
import json
import os
import pathlib
import subprocess
import sys
import tempfile
from collections.abc import Callable, Mapping, Sequence
from typing import Any

SUMMARY = "evidence_bound_reasoning_summary"
OUT_ENV = "SROS_GATE_DIFFERENTIAL_OUT"
EVALUATOR = "evaluate_second_opportunity_output_v1_3"
PLUGIN = "second_opportunity_gate_differential"
DOMAINS = ("COMMON", "BAND", "ABOVE", "RAISED")


def bounds() -> tuple[int, int]:
    """The summary's maxLength under v1.1.0 and under v1.2.0, read from the live schemas."""
    from sros_opportunity.second_opportunity import SECOND_OPPORTUNITY_OUTPUT_SCHEMA_V1_1
    from sros_opportunity.second_opportunity_schema_v1_2 import (
        SECOND_OPPORTUNITY_OUTPUT_SCHEMA_V1_2,
    )

    def bound(schema: Mapping[str, Any]) -> int:
        return int(schema["properties"][SUMMARY]["maxLength"])

    return bound(SECOND_OPPORTUNITY_OUTPUT_SCHEMA_V1_1), bound(
        SECOND_OPPORTUNITY_OUTPUT_SCHEMA_V1_2
    )


def _prefixes() -> tuple[str, str]:
    from sros_opportunity.second_opportunity_gate_v1_4 import (
        PREDECESSOR_STRUCTURAL_REASON_PREFIX,
        STRUCTURAL_REASON_PREFIX,
    )

    return PREDECESSOR_STRUCTURAL_REASON_PREFIX, STRUCTURAL_REASON_PREFIX


def _split(reasons: Sequence[str], prefix: str) -> tuple[list[str], list[str]]:
    """The leading structural reasons with their prefix removed, and every reason after them."""
    count = 0
    while count < len(reasons) and reasons[count].startswith(prefix):
        count += 1
    return [r[len(prefix) :] for r in reasons[:count]], list(reasons[count:])


def domain(output: object) -> str:
    old, new = bounds()
    value = output.get(SUMMARY) if isinstance(output, Mapping) else None
    if not isinstance(value, str) or len(value) <= old:
        return "COMMON"
    return "BAND" if len(value) <= new else "ABOVE"


def expected_structural(old_structural: Sequence[str], output: object) -> list[str]:
    """What v1.4.0's structural reasons must be, given v1.3.0's, when one leaf is all that moved."""
    old, new = bounds()
    value = output.get(SUMMARY) if isinstance(output, Mapping) else None
    if not isinstance(value, str) or len(value) <= old:
        return list(old_structural)
    stale = f"{SUMMARY}: {len(value)} characters exceeds maxLength {old}"
    fresh = f"{SUMMARY}: {len(value)} characters exceeds maxLength {new}"
    expected: list[str] = []
    for reason in old_structural:
        if reason != stale:
            expected.append(reason)
        elif len(value) > new:
            expected.append(fresh)
    return expected


def compare(v1_3: Any, v1_4: Any, output: object) -> dict[str, Any]:
    """One pair of verdicts on the same arguments, classified."""
    from sros_opportunity.second_opportunity_gate_v1_4 import SECOND_OPPORTUNITY_GATE_VERSION_V1_4

    old_prefix, new_prefix = _prefixes()
    old_structural, old_rest = _split(tuple(v1_3.refusal_reasons), old_prefix)
    new_structural, new_rest = _split(tuple(v1_4.refusal_reasons), new_prefix)
    semantic = old_rest == new_rest and v1_3.audit == v1_4.audit and v1_3.notes == v1_4.notes
    structural = new_structural == expected_structural(old_structural, output)
    consistent = (
        v1_4.persist is (not v1_4.refusal_reasons)
        and v1_4.gate_version == SECOND_OPPORTUNITY_GATE_VERSION_V1_4
    )
    record: dict[str, Any] = {
        "domain": domain(output),
        "semantic_equal": semantic,
        "structural_as_expected": structural,
        "consistent": consistent,
        "persist_v1_3": v1_3.persist,
        "persist_v1_4": v1_4.persist,
    }
    if not (semantic and structural and consistent):
        record["reasons_v1_3"] = list(v1_3.refusal_reasons)
        record["reasons_v1_4"] = list(v1_4.refusal_reasons)
    return record


def pair(
    v1_3: Callable[..., Any],
    v1_4: Callable[..., Any],
    args: Sequence[object],
    kwargs: Mapping[str, object],
) -> tuple[dict[str, Any], Any, Any, BaseException | None]:
    """Both gates on the same arguments, each once.

    Returns (the record, v1.3.0's verdict, v1.4.0's verdict, v1.3.0's exception); a verdict is None
    where its gate raised.
    """
    output = args[0] if args else kwargs.get("output")
    try:
        old = v1_3(*args, **kwargs)
    except Exception as error:
        try:
            v1_4(*args, **kwargs)
        except Exception as successor_error:
            same = type(successor_error) is type(error)
        else:
            same = False
        record = {
            "domain": "RAISED",
            "raised": type(error).__name__,
            "semantic_equal": same,
            "structural_as_expected": True,
            "consistent": True,
        }
        return record, None, None, error
    try:
        new = v1_4(*args, **kwargs)
    except Exception as error:
        record = {
            "domain": domain(output),
            "v1_4_raised": type(error).__name__,
            "semantic_equal": False,
            "structural_as_expected": False,
            "consistent": False,
        }
        return record, old, None, None
    return compare(old, new, output), old, new, None


def divergent(record: Mapping[str, Any]) -> bool:
    return not (
        record["semantic_equal"] and record["structural_as_expected"] and record["consistent"]
    )


def summarize(records: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    return {
        "EVALUATOR_CALLS": len(records),
        "BY_DOMAIN": {d: sum(1 for r in records if r["domain"] == d) for d in DOMAINS},
        "PERSIST_CHANGED_BY_DOMAIN": {
            d: sum(
                1
                for r in records
                if r["domain"] == d and r.get("persist_v1_3") != r.get("persist_v1_4")
            )
            for d in DOMAINS
        },
        "COMMON_DOMAIN_SEMANTIC_DIVERGENCES": sum(
            1 for r in records if r["domain"] == "COMMON" and divergent(r)
        ),
        "NON_STRUCTURAL_SEMANTIC_DIVERGENCES": sum(1 for r in records if not r["semantic_equal"]),
        "STRUCTURAL_DIVERGENCES_BEYOND_THE_ONE_BOUND": sum(
            1 for r in records if not r["structural_as_expected"]
        ),
        "INCONSISTENT_V1_4_VERDICTS": sum(1 for r in records if not r["consistent"]),
        "DIVERGENCES": sum(1 for r in records if divergent(r)),
    }


# --------------------------------------------------------------------------- the matrix replay


def replay_matrix(test_file: pathlib.Path, suite: pathlib.Path) -> dict[str, Any]:
    """Run gate v1.3.0's test file in its own suite, as CI runs it, with the spy installed.

    A separate interpreter, so the patch cannot leak into the caller and the suite's `tests` package
    is imported the way `run_pytest_suites.py` imports it.
    """
    scripts = pathlib.Path(__file__).resolve().parent
    with tempfile.TemporaryDirectory() as directory:
        out = pathlib.Path(directory) / "differential.json"
        env = dict(os.environ)
        env[OUT_ENV] = str(out)
        env["PYTHONPATH"] = os.pathsep.join(
            p for p in (str(scripts), env.get("PYTHONPATH", "")) if p
        )
        process = subprocess.run(  # noqa: S603 -- our own interpreter, our own file
            [
                sys.executable,
                "-m",
                "pytest",
                test_file.relative_to(suite).as_posix(),
                "-q",
                "-p",
                "no:cacheprovider",
                "-p",
                PLUGIN,
            ],
            cwd=suite,
            env=env,
            capture_output=True,
            text=True,
            check=False,
        )
        if not out.exists():
            tail = (process.stdout + process.stderr)[-2000:]
            raise RuntimeError(
                f"the matrix replay wrote no result (exit {process.returncode}): {tail}"
            )
        result: dict[str, Any] = json.loads(out.read_text(encoding="utf-8"))
    result["returncode"] = process.returncode
    return result


_STATE: dict[str, Any] = {
    "records": [],
    "patched": [],
    "tests": {"passed": 0, "failed": 0, "skipped": 0},
    "current": None,
    "reaching": set(),
}


def pytest_runtest_setup(item: Any) -> None:
    _STATE["current"] = item.nodeid


def pytest_collection_finish(session: Any) -> None:
    from sros_opportunity import second_opportunity_gate_v1_3 as v1_3
    from sros_opportunity import second_opportunity_gate_v1_4 as v1_4

    original = v1_3.evaluate_second_opportunity_output_v1_3
    successor = v1_4.evaluate_second_opportunity_output_v1_4

    @functools.wraps(original)
    def spy(*args: object, **kwargs: object) -> Any:
        record, verdict, _successor_verdict, error = pair(original, successor, args, kwargs)
        _STATE["records"].append(record)
        if _STATE["current"] is not None:
            _STATE["reaching"].add(_STATE["current"])
        if error is not None:
            raise error
        return verdict

    for name, module in list(sys.modules.items()):
        # v1.4.0 holds its own reference to the original; replacing it would recurse.
        if module is None or name in (v1_4.__name__, __name__):
            continue
        if vars(module).get(EVALUATOR) is original:
            setattr(module, EVALUATOR, spy)
            _STATE["patched"].append(name)


def pytest_runtest_logreport(report: Any) -> None:
    tests = _STATE["tests"]
    if report.when == "call" or report.outcome in ("failed", "skipped"):
        tests[report.outcome] = tests.get(report.outcome, 0) + 1


def pytest_sessionfinish(session: Any, exitstatus: int) -> None:
    target = os.environ.get(OUT_ENV)
    if not target:
        return
    records = _STATE["records"]
    payload = {
        "exitstatus": int(exitstatus),
        "tests": dict(_STATE["tests"]),
        "patched_modules": sorted(_STATE["patched"]),
        "tests_reaching_the_evaluator": len(_STATE["reaching"]),
        "summary": summarize(records),
        "divergent_examples": [r for r in records if divergent(r)][:5],
    }
    pathlib.Path(target).write_text(json.dumps(payload, indent=2), encoding="utf-8")
