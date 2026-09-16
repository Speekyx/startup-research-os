"""Mission 1.85.2 (roadmap N05). Declared-dependent lineages never count as established independence.

Algorithm 1.0.0 counted every support group that was not the unknown bucket toward the Repeated Signal and
Strong Multi-Source thresholds, so two copies of two origins read as two independent observations. The
repair counts only INDEPENDENT groups. These tests hold it to its contract against the predecessor record
written under 1.0.0 before `levels.py` changed:

* the brief's fixed levels, before and after;
* nothing but the level fields moves: masses, score, groups, counts, warnings and explanation are
  byte-identical, and no level rises;
* only the two independence thresholds' reasons may differ, and evidence without a declared lineage keeps
  every reason byte-identical;
* canonical output is independent of input order, and the four masses still sum to one.
"""

from __future__ import annotations

import hashlib
import json
import pathlib
import random
import unittest

from sros_evidence_aggregation import REFERENCE_PROFILE_V1, GroupKind

from .independence_level_cases import (
    CASES,
    EXPECTED_LEVELS,
    dependent,
    item,
    permutations,
    run,
    unknown,
)

REPO_ROOT = pathlib.Path(__file__).resolve().parents[4]
PREDECESSOR = json.loads(
    (
        REPO_ROOT / "docs" / "data" / "evidence-aggregation-independence-level-predecessor-v1.json"
    ).read_text("utf-8")
)
LEVEL_FIELDS = {"algorithm_version", "evidence_level", "label", "reasons", "blocked_reasons"}
THRESHOLD_MARKERS = ("Repeated Signal", "Strong Multi-Source", "independent groups across")
CLAUSE = "declared-dependent lineage group(s) do not count"


def _current(case_id: str) -> dict:
    return json.loads(run(CASES[case_id]).canonical_json())


class TestPredecessorRecord(unittest.TestCase):
    def test_the_record_was_written_under_algorithm_1_0_0(self) -> None:
        self.assertEqual(PREDECESSOR["algorithm_version"], "1.0.0")
        for case_id, result in PREDECESSOR["cases"].items():
            self.assertEqual(result["algorithm_version"], "1.0.0", case_id)

    def test_the_case_digests_recompute(self) -> None:
        for case_id, result in PREDECESSOR["cases"].items():
            canonical = json.dumps(result, sort_keys=True, separators=(",", ":"))
            digest = hashlib.sha256(canonical.encode("utf-8")).hexdigest()
            self.assertEqual(digest, PREDECESSOR["case_digests"][case_id], case_id)

    def test_the_record_covers_exactly_the_current_cases(self) -> None:
        self.assertEqual(set(PREDECESSOR["cases"]), set(CASES))

    def test_the_real_rows_were_all_unknown(self) -> None:
        real = PREDECESSOR["real_rows"]
        self.assertEqual(real["independence_states"], {"UNKNOWN": real["evidence_rows"]})


class TestRequiredLevels(unittest.TestCase):
    def test_the_brief_levels_before_and_after(self) -> None:
        for case_id, (before, after) in EXPECTED_LEVELS.items():
            with self.subTest(case_id):
                self.assertEqual(PREDECESSOR["cases"][case_id]["evidence_level"], before)
                self.assertEqual(_current(case_id)["evidence_level"], after)

    def test_levels_four_and_five_are_unchanged(self) -> None:
        for case_id in ("C11_single_dependent_market_activity", "A07_dependent_direct_validation"):
            with self.subTest(case_id):
                self.assertEqual(
                    _current(case_id)["evidence_level"],
                    PREDECESSOR["cases"][case_id]["evidence_level"],
                )


class TestNothingElseMoves(unittest.TestCase):
    def test_non_level_fields_are_byte_identical(self) -> None:
        for case_id, before in PREDECESSOR["cases"].items():
            with self.subTest(case_id):
                after = _current(case_id)
                strip = lambda d: {k: v for k, v in d.items() if k not in LEVEL_FIELDS}  # noqa: E731
                self.assertEqual(strip(before), strip(after))

    def test_no_level_rises(self) -> None:
        for case_id, before in PREDECESSOR["cases"].items():
            with self.subTest(case_id):
                self.assertLessEqual(_current(case_id)["evidence_level"], before["evidence_level"])

    def test_only_independence_threshold_reasons_move(self) -> None:
        for case_id, before in PREDECESSOR["cases"].items():
            after = _current(case_id)
            for field in ("reasons", "blocked_reasons"):
                with self.subTest(case_id=case_id, field=field):
                    moved = set(before[field]) ^ set(after[field])
                    self.assertTrue(all(any(m in r for m in THRESHOLD_MARKERS) for r in moved))

    def test_evidence_without_a_declared_lineage_keeps_every_reason(self) -> None:
        for case_id, items in CASES.items():
            if any(i.independence_group_id for i in items):
                continue
            with self.subTest(case_id):
                before, after = PREDECESSOR["cases"][case_id], _current(case_id)
                self.assertEqual(before["reasons"], after["reasons"])
                self.assertEqual(before["blocked_reasons"], after["blocked_reasons"])
                self.assertEqual(before["evidence_level"], after["evidence_level"])

    def test_the_unknown_only_message_is_byte_identical(self) -> None:
        self.assertEqual(
            _current("C01_all_unknown")["blocked_reasons"],
            PREDECESSOR["cases"]["C01_all_unknown"]["blocked_reasons"],
        )
        self.assertIn(
            "found 0 (plus 1 unknown-provenance group, which does not count)",
            _current("C01_all_unknown")["blocked_reasons"][0],
        )


class TestTheDeclaredLineageClause(unittest.TestCase):
    def test_a_blocked_threshold_names_the_uncounted_lineages(self) -> None:
        reasons = _current("C02_one_dependent_lineage_plus_unknown")["blocked_reasons"][0]
        self.assertIn("found 0 (plus 1 unknown-provenance group, which does not count)", reasons)
        self.assertIn(f"1 {CLAUSE}", reasons)
        self.assertIn("not established as independent of each other", reasons)
        self.assertIn("established independence", reasons)

    def test_the_clause_appears_only_where_a_supporting_lineage_exists(self) -> None:
        for case_id, items in CASES.items():
            with self.subTest(case_id):
                result = run(items)
                has_lineage = any(
                    g.kind is GroupKind.DECLARED_DEPENDENT for g in result.groups.support
                )
                text = " ".join(result.level.blocked_reasons)
                # The clause rides on a blocked independence threshold. Levels 4 and 5 come from
                # category, so a level-4 record can still have Repeated Signal blocked.
                reached_multi_source = any(
                    "independent groups across" in r for r in result.level.reasons
                )
                expected = has_lineage and not reached_multi_source
                self.assertEqual(CLAUSE in text, expected)

    def test_the_clause_is_bounded_and_carries_no_lineage_name(self) -> None:
        items = [dependent(f"d{n}", "x" * 500 + str(n)) for n in range(40)]
        text = run(items).level.blocked_reasons[0]
        self.assertIn(f"40 {CLAUSE}", text)
        self.assertNotIn("x" * 50, text)
        self.assertLess(len(text), 400)

    def test_dependent_lineages_are_never_called_independent_sources(self) -> None:
        level = run(CASES["C04_three_dependent_lineages_two_families"]).level
        self.assertNotIn("independent source", " ".join(level.blocked_reasons))
        self.assertNotIn("independent groups across", " ".join(level.reasons))


class TestProperties(unittest.TestCase):
    def test_every_case_is_order_invariant(self) -> None:
        for case_id, items in CASES.items():
            with self.subTest(case_id):
                outputs = {run(order).canonical_json() for order in permutations(items)}
                self.assertEqual(len(outputs), 1)

    def test_the_masses_sum_to_one(self) -> None:
        for case_id, items in CASES.items():
            with self.subTest(case_id):
                self.assertTrue(run(items).masses.sums_to_one())

    def test_levels_two_and_three_count_only_independent_groups(self) -> None:
        """A seeded model check over random mixes of the three states."""
        thresholds = REFERENCE_PROFILE_V1.level_thresholds
        rng = random.Random(18520)  # noqa: S311 -- a seeded fuzz, not a secret
        states = ("independent", "dependent", "unknown")
        for trial in range(300):
            items = []
            for n in range(rng.randint(1, 7)):
                kind = rng.choice(states)
                family = rng.choice(("f1", "f2", "f3"))
                eid = f"t{trial}-{n}"
                if kind == "independent":
                    items.append(item(eid, family=family))
                elif kind == "dependent":
                    items.append(dependent(eid, rng.choice(("g1", "g2", "g3")), family=family))
                else:
                    items.append(unknown(eid, family=family))
            result = run(items)
            independent = sum(1 for g in result.groups.support if g.kind is GroupKind.INDEPENDENT)
            families = {i.source_family for i in items}
            expected = 1
            if independent >= thresholds.repeated_signal_min_groups:
                expected = 2
                if (
                    independent >= thresholds.multi_source_min_groups
                    and len(families) >= thresholds.multi_source_min_families
                ):
                    expected = 3
            with self.subTest(trial=trial):
                self.assertEqual(result.level.level, expected)


if __name__ == "__main__":
    unittest.main()
