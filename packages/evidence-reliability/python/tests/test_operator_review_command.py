"""The operator review command's refusals, over no database and no network.

Mission 1.15.13. The command is
`infrastructure/scripts/record_reliability_assessment.py`; it is loaded here by
path because `infrastructure/scripts` is not a package, and only its **pure
validation** is exercised. Nothing below opens a connection: `psycopg` is
imported inside `main()` precisely so this suite can run in the zero-dependency
path (ADR-009).

**What this suite is really protecting.** Mission 1.15.12 stopped because the
framework reserves one act to an accountable person. A tool that lets a person
record that act is one careless default away from performing it for them, and
every test here names a specific way that could happen:

    a value nobody entered          -> refused
    a reviewer nobody can ask       -> refused
    a limitation nobody wrote       -> refused
    a rationale nobody wrote        -> refused
    a value outside the scale       -> refused
    an assessment resting on nothing retrieved -> refused

**No test here encodes a plausible production reliability number.** Where a
value is needed it is `0.42`, which nobody will mistake for a judgement and
nobody will copy into a real review.
"""

from __future__ import annotations

import copy
import importlib.util
import pathlib
import unittest

_SPEC = importlib.util.spec_from_file_location(
    "record_reliability_assessment",
    pathlib.Path(__file__).resolve().parents[4]
    / "infrastructure"
    / "scripts"
    / "record_reliability_assessment.py",
)
assert _SPEC and _SPEC.loader
command = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(command)


def review(**overrides) -> dict:
    """A COMPLETE review file, as a person would have written it.

    Every judgement field carries obviously-a-fixture text, so no test can be
    read as endorsing a value or a wording.
    """
    packet = command.PACKETS["ted-eu-procurement-contrast"]
    base = {
        "scope": dict(packet["scope"]),
        "origin": "HUMAN_REVIEW",
        "reliability": 0.42,
        "reviewed_by": "A Named Person",
        "rationale": "A fixture rationale standing in for a real reviewer's reasoning.",
        "stated_limitation": "A fixture limitation standing in for a real reviewer's bound.",
        "basis": copy.deepcopy(packet["basis"]),
    }
    base.update(overrides)
    return base


class TestTheJudgementMustBeSupplied(unittest.TestCase):
    """§3 and §6 of the mission brief: nothing here has a default."""

    def test_a_complete_review_builds(self):
        assessment = command._build(review())
        self.assertEqual(assessment.reliability, 0.42)
        self.assertEqual(assessment.reviewed_by, "A Named Person")
        self.assertEqual(assessment.origin.value, "HUMAN_REVIEW")

    def test_a_missing_reliability_is_refused_rather_than_defaulted(self):
        with self.assertRaises(ValueError) as caught:
            command._build(review(reliability=None))
        self.assertIn("reliability", str(caught.exception))

    def test_an_empty_reviewer_is_refused(self):
        with self.assertRaises(ValueError):
            command._build(review(reviewed_by=""))

    def test_an_empty_stated_limitation_is_refused(self):
        """The field that stops a number being unarguable.

        The guide asks a reviewer to write the failure mode first; a value with
        no stated limitation is a number nobody can argue with, which is the
        shape a wrong one keeps for longest.
        """
        with self.assertRaises(ValueError):
            command._build(review(stated_limitation=""))

    def test_an_empty_rationale_is_refused(self):
        with self.assertRaises(ValueError):
            command._build(review(rationale=""))

    def test_the_template_has_every_judgement_field_blank(self):
        """The packet supplies FACTS. It must never supply a judgement.

        If this test starts failing because a field acquired a helpful default,
        the tool has begun making the decision it exists to record.
        """
        template = command._template(command.PACKETS["ted-eu-procurement-contrast"])
        self.assertIsNone(template["reliability"])
        self.assertEqual(template["reviewed_by"], "")
        self.assertEqual(template["rationale"], "")
        self.assertEqual(template["stated_limitation"], "")

    def test_no_packet_proposes_a_value_or_a_limitation(self):
        for name, packet in command.PACKETS.items():
            flat = str(packet).lower()
            self.assertNotIn("reliability_value", flat, name)
            self.assertNotIn("suggested_value", flat, name)
            self.assertNotIn("recommended", flat, name)
            self.assertNotIn("reliability", packet, name)


class TestTheReviewerIsAPerson(unittest.TestCase):
    """§5: the field a later reader uses to ask who decided this, and why."""

    def test_impersonal_identifiers_are_refused(self):
        for name in ("operator", "system", "admin", "claude", "ai", "script", "OPERATOR"):
            with self.subTest(name=name), self.assertRaises(ValueError) as caught:
                command._build(review(reviewed_by=name))
            self.assertIn("names nobody", str(caught.exception))

    def test_a_real_name_is_accepted(self):
        self.assertEqual(command._build(review(reviewed_by="T. Chm")).reviewed_by, "T. Chm")


class TestTheContractStillDoesTheRest(unittest.TestCase):
    """The command validates the FILE; the model validates the assessment.

    These assert the command does not weaken anything the model already
    guarantees, by letting a bad file through to it.
    """

    def test_a_value_outside_the_scale_is_refused(self):
        for value in (-0.1, 1.5, 2):
            with self.subTest(value=value), self.assertRaises(ValueError):
                command._build(review(reliability=value))

    def test_a_non_numeric_value_is_refused(self):
        for value in ("0.9", True, [0.9]):
            with self.subTest(value=value), self.assertRaises(ValueError):
                command._build(review(reliability=value))

    def test_an_assessment_resting_on_nothing_retrieved_is_refused(self):
        with self.assertRaises(ValueError):
            command._build(review(basis=[]))

    def test_a_human_review_may_not_name_a_calibration_dataset(self):
        """Human review is not calibration, however careful it was."""
        with self.assertRaises(ValueError):
            command._build(review(calibration_dataset_ref="some-outcome-set"))

    def test_an_incomplete_scope_is_refused(self):
        scope = dict(command.PACKETS["ted-eu-procurement-contrast"]["scope"])
        scope["resource_id"] = ""
        with self.assertRaises(ValueError):
            command._build(review(scope=scope))


class TestNoThresholdVocabulary(unittest.TestCase):
    """§6: the contract has no label scale and this tool must not grow one."""

    def test_the_command_names_no_threshold_label(self):
        text = pathlib.Path(command.__file__).read_text(encoding="utf-8").lower()
        for label in ("authoritative", "= good", "= uncertain", "0.9 =", "0.7 ="):
            self.assertNotIn(label, text, label)


class TestTheScopeIsTheOneUnderReview(unittest.TestCase):
    """The packet must describe the real Evidence row's scope, not a near miss."""

    def test_the_ted_packet_matches_the_live_evidence_scope(self):
        from sros_contracts import ClaimType
        from sros_evidence_reliability import ReliabilityScope

        built = command._build(review()).scope
        expected = ReliabilityScope(
            source_id="ted-eu",
            resource_id="notices/eforms-contract-and-award",
            record_kind_id="procurement_notice",
            claim_type=ClaimType.OBSERVED,
            proposition_kind="source_reported_procurement_value_contrast",
        )
        self.assertEqual(built.key, expected.key)


if __name__ == "__main__":
    unittest.main()
