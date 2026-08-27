"""Shared conformance suite (Python side).

Reads packages/contracts/conformance/cases.json -- the SAME file the TypeScript
suite reads. If the two implementations ever disagree, one of these suites goes
red. That is what makes "TS and Python contracts are synchronized" a tested
property rather than a claim.

Stdlib unittest, so it runs with no install. pytest collects it too.
"""

from __future__ import annotations

import dataclasses
import json
import pathlib
import unittest

from sros_contracts import (
    ClaimType,
    ContractError,
    MarketScope,
    RegistryRef,
    ResearchContext,
    ResearchSessionStatus,
)
from sros_contracts.numeric import check_numeric

ROOT = pathlib.Path(__file__).resolve().parents[2]
CASES = json.loads((ROOT / "conformance" / "cases.json").read_text(encoding="utf-8"))


class NumericConformance(unittest.TestCase):
    def test_valid_and_invalid_ranges(self) -> None:
        for type_name, cases in CASES["numeric"].items():
            for value in cases["valid"]:
                with self.subTest(type=type_name, value=value, expect="valid"):
                    check_numeric(type_name, value)
            for value in cases["invalid"]:
                with (
                    self.subTest(type=type_name, value=value, expect="invalid"),
                    self.assertRaises(ContractError),
                ):
                    check_numeric(type_name, value)

    def test_confidence_and_score_are_not_interchangeable(self) -> None:
        """The single most likely silent numeric bug in the system."""
        check_numeric("Score", 82)
        with self.assertRaises(ContractError):
            check_numeric("Confidence", 82)
        check_numeric("Confidence", 0.82)
        with self.assertRaises(ContractError):
            check_numeric("Score", 0.82)

    def test_booleans_are_not_numbers(self) -> None:
        with self.assertRaises(ContractError):
            check_numeric("Score", True)


class MarketScopeConformance(unittest.TestCase):
    def test_valid_cases_canonicalize(self) -> None:
        for case in CASES["market_scope"]["valid"]:
            with self.subTest(case=case["name"]):
                scope = MarketScope.from_json(case["input"])
                self.assertEqual(scope.to_json(), case["canonical"])
                self.assertEqual(scope.key(), case["key"])

    def test_invalid_cases_rejected(self) -> None:
        for case in CASES["market_scope"]["invalid"]:
            with (
                self.subTest(case=case["name"], reason=case["reason"]),
                self.assertRaises(ContractError),
            ):
                MarketScope.from_json(case["input"])

    def test_equality_cases(self) -> None:
        for case in CASES["market_scope"]["equality"]:
            with self.subTest(case=case["name"]):
                a = MarketScope.from_json(case["a"])
                b = MarketScope.from_json(case["b"])
                self.assertEqual(a == b, case["equal"])
                self.assertEqual(a.key() == b.key(), case["equal"])

    def test_scope_is_hashable_and_usable_as_a_key(self) -> None:
        a = MarketScope.from_json({"type": "MULTI_COUNTRY", "countries": ["us", "FR"]})
        b = MarketScope.from_json({"type": "MULTI_COUNTRY", "countries": ["FR", "US"]})
        self.assertEqual(len({a, b}), 1)

    def test_segment_is_not_implemented(self) -> None:
        """A-12 is deliberately open. A SEGMENT scope must fail loudly, with a hint."""
        with self.assertRaises(ContractError) as ctx:
            MarketScope.from_json({"type": "SEGMENT"})
        self.assertIn("A-12", str(ctx.exception))


class ClosedEnumConformance(unittest.TestCase):
    def test_claim_type_exact_values(self) -> None:
        self.assertEqual(
            [m.value for m in ClaimType],
            ["OBSERVED", "INFERRED", "PREDICTED", "RECOMMENDED", "HYPOTHESIS"],
        )
        for value in CASES["claim_type"]["valid"]:
            ClaimType(value)
        for value in CASES["claim_type"]["invalid"]:
            with self.subTest(value=value), self.assertRaises(ValueError):
                ClaimType(value)

    def test_hypothesis_is_first_class(self) -> None:
        """Without it the anti-hallucination rule has nowhere to put a claim."""
        self.assertIs(ClaimType("HYPOTHESIS"), ClaimType.HYPOTHESIS)

    def test_research_session_status_values(self) -> None:
        for value in CASES["research_session_status"]["valid"]:
            ResearchSessionStatus(value)
        for value in CASES["research_session_status"]["invalid"]:
            with self.subTest(value=value), self.assertRaises(ValueError):
                ResearchSessionStatus(value)

    def test_no_invented_lifecycle_states(self) -> None:
        """Budget exhaustion is COMPLETED with reduced completeness, not a status."""
        names = {m.value for m in ResearchSessionStatus}
        self.assertNotIn("BUDGET_EXHAUSTED", names)
        self.assertNotIn("PARTIAL", names)
        self.assertIn("COMPLETED", names)


class RegistryConformance(unittest.TestCase):
    def test_valid_refs(self) -> None:
        for case in CASES["registry_ref"]["valid"]:
            with self.subTest(case=case):
                ref = RegistryRef.from_json(case)
                self.assertEqual(ref.to_json(), {"id": case["id"], "registry": case["registry"]})

    def test_invalid_refs(self) -> None:
        for case in CASES["registry_ref"]["invalid"]:
            with self.subTest(reason=case["reason"]), self.assertRaises(ContractError):
                RegistryRef.from_json(case["case"])

    def test_closed_enums_are_not_registries(self) -> None:
        """A-07: ClaimType is an enum. Referencing it as a registry must fail."""
        with self.assertRaises(ContractError):
            RegistryRef(registry="claim_type", id="observed")


class ResearchContextConformance(unittest.TestCase):
    def test_valid_cases_produce_expected_canonical_json(self) -> None:
        for case in CASES["research_context"]["valid"]:
            with self.subTest(case=case["name"]):
                ctx = ResearchContext.from_json(case["input"])
                self.assertEqual(ctx.canonical_json(), case["canonical_json"])

    def test_invalid_cases_rejected(self) -> None:
        for case in CASES["research_context"]["invalid"]:
            with (
                self.subTest(case=case["name"], reason=case["reason"]),
                self.assertRaises(ContractError),
            ):
                ResearchContext.from_json(case["input"])

    def test_snapshot_is_immutable(self) -> None:
        """Ontology V2 §11.3: editing a context must never mutate a past snapshot."""
        original = ResearchContext.from_json({"market_scope": {"type": "GLOBAL"}})
        snapshot = original.canonical_json()
        snapshot_hash = original.snapshot_hash()

        changed = original.with_changes(audience="indie devs")

        self.assertEqual(original.canonical_json(), snapshot)
        self.assertEqual(original.snapshot_hash(), snapshot_hash)
        self.assertNotEqual(changed.canonical_json(), snapshot)
        self.assertIsNone(original.audience)

    def test_frozen_dataclass_rejects_attribute_assignment(self) -> None:
        ctx = ResearchContext.from_json({"market_scope": {"type": "GLOBAL"}})
        with self.assertRaises(dataclasses.FrozenInstanceError):
            ctx.audience = "nope"  # type: ignore[misc]

    def test_identical_specifications_hash_identically(self) -> None:
        a = ResearchContext.from_json(
            {"market_scope": {"type": "MULTI_COUNTRY", "countries": ["us", "fr"]}}
        )
        b = ResearchContext.from_json(
            {"market_scope": {"type": "MULTI_COUNTRY", "countries": ["FR", "US"]}}
        )
        self.assertEqual(a.snapshot_hash(), b.snapshot_hash())


class BlockedWorkGuard(unittest.TestCase):
    """D-03: no aggregation semantics may leak into contracts."""

    def test_no_forbidden_aggregation_fields_in_contracts(self) -> None:
        source_root = ROOT / "python" / "sros_contracts"
        forbidden = CASES["forbidden_fields"]["names"]
        offenders: list[str] = []
        for path in sorted(source_root.rglob("*.py")):
            text = path.read_text(encoding="utf-8")
            for name in forbidden:
                if name in text:
                    offenders.append(f"{path.name}: {name}")
        self.assertEqual(offenders, [], f"D-03 leakage into contracts: {offenders}")


if __name__ == "__main__":
    unittest.main()
