"""Mission 1.76.2. One question, and it is the one that was not answered.

Four things this file defends.

A NEW QUESTION IS A NEW ACTION. GP-R2-Q1's two approvals are both spent and both name a
different content digest and a different question id, so neither reaches this packet. The
gate asserts that live, so an edit that retargeted a spent approval fails here.

THE THREAD IS WHAT IS BOUND, BECAUSE NO ADDRESS IS KNOWN. The sender of the reply being
answered is NOT_ESTABLISHED, so an address in the recipient field would be invented. A
reply inside a thread inherits its recipient, so the digest binds the thread instead --
its subject, the prior packet's digest and the prior reply's digest -- which pins the
conversation rather than a mailbox.

ONE QUESTION, AND NOT THE SETTLED ONE. The last enquiry was compound and came back with an
answer to the clause that was already closed. This one carries a single question mark, says
nothing about commercial use, and names HEAD, third-party and "do not own or operate".

RESPONSIVENESS AND AUTHORITY STAY SEPARATE GATES. The earlier sender being unestablished
does not block preparing this packet, and preparing it does not establish them.
"""

from __future__ import annotations

import copy
import hashlib
import importlib.util
import json
import pathlib
import unittest

REPO_ROOT = pathlib.Path(__file__).resolve().parents[4]
DATA = REPO_ROOT / "docs" / "data"
SCRIPTS = REPO_ROOT / "infrastructure" / "scripts"

PACKET = DATA / "globalping-r2b-enquiry-packet-v1.json"
V1_PACKET = DATA / "globalping-r2-enquiry-packet-v1.json"
V2_PACKET = DATA / "globalping-r2-enquiry-packet-v2.json"
V1_APPROVAL = DATA / "globalping-r2-dispatch-approval-v1.json"
V2_APPROVAL = DATA / "globalping-r2-v2-dispatch-approval-v1.json"
FROZEN_REPLY = DATA / "globalping-r2-provider-reply-v1.json"
THIRD_PARTY = DATA / "globalping-third-party-target-scope-review-v1.json"
QUALIFICATION = DATA / "globalping-counterpart-qualification-v3.json"
RENDERER = SCRIPTS / "render_r2b_followup_packet.py"
PAGE = DATA / "globalping-r2b-followup-packet-v1.md"
MANIFEST = REPO_ROOT / "PROJECT_MANIFEST.md"
CI = REPO_ROOT / ".github" / "workflows" / "ci.yml"


def load(path: pathlib.Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def gate():
    spec = importlib.util.spec_from_file_location("render_r2b_followup_packet", RENDERER)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class TestItIsANewQuestionNoSpentApprovalReaches(unittest.TestCase):
    def setUp(self):
        self.packet = load(PACKET)

    def test_it_answers_to_its_own_hash(self):
        module = gate()
        self.assertEqual(
            module._digest(self.packet, self.packet["hash_covers"]),
            self.packet["content_sha256"],
        )

    def test_its_digest_and_id_differ_from_both_earlier_packets(self):
        for other in (load(V1_PACKET), load(V2_PACKET)):
            with self.subTest(packet=other["question_id"]):
                self.assertNotEqual(self.packet["content_sha256"], other["content_sha256"])
                self.assertNotEqual(self.packet["question_id"], other["question_id"])

    def test_neither_spent_approval_names_it(self):
        for path in (V1_APPROVAL, V2_APPROVAL):
            action = load(path)["approved_action"]
            with self.subTest(approval=path.name):
                self.assertNotEqual(
                    action["approved_content_sha256"], self.packet["content_sha256"]
                )
                self.assertNotEqual(action["approves"], self.packet["question_id"])

    def test_it_names_both_spent_approvals_as_unable_to_authorise_it(self):
        named = {e["record"] for e in self.packet["prior_approvals_that_cannot_authorise_this"]}
        self.assertEqual(len(named), 2)
        self.assertTrue(self.packet["requires_a_new_explicit_operator_approval"])

    def test_the_earlier_packets_were_not_edited(self):
        for other in (load(V1_PACKET), load(V2_PACKET)):
            with self.subTest(packet=other["question_id"]):
                self.assertEqual(other["send_status"], "NOT_AUTHORIZED")
                self.assertFalse(other["operator_approval_recorded"])


class TestTheThreadIsWhatIsBound(unittest.TestCase):
    def setUp(self):
        self.packet = load(PACKET)

    def test_the_recipient_is_a_sentinel_and_not_an_address(self):
        self.assertEqual(self.packet["recipient"], gate().RECIPIENT_SENTINEL)
        self.assertNotIn("@", self.packet["recipient"])
        self.assertFalse(self.packet["recipient_is_an_address"])
        self.assertIn("NOT_ESTABLISHED", self.packet["why_the_recipient_is_not_an_address"])

    def test_the_recipient_is_not_hashed(self):
        self.assertNotIn("recipient", self.packet["hash_covers"])
        self.assertIn("recipient", self.packet["hash_excludes"])

    def test_the_thread_binding_names_the_real_prior_packet_and_reply(self):
        binding = self.packet["thread_binding"]
        self.assertEqual(binding["thread_subject"], load(V2_PACKET)["subject"])
        self.assertEqual(
            binding["prior_enquiry_packet_content_sha256"], load(V2_PACKET)["content_sha256"]
        )
        self.assertEqual(
            binding["prior_reply_body_sha256"], load(FROZEN_REPLY)["reply"]["body_sha256"]
        )

    def test_the_thread_is_bound_by_the_hash(self):
        self.assertIn("thread_binding", self.packet["hash_covers"])
        self.assertIn("subject", self.packet["hash_covers"])


class TestItAsksOneQuestionAndNotTheSettledOne(unittest.TestCase):
    def setUp(self):
        self.packet = load(PACKET)

    def test_the_body_carries_exactly_one_question(self):
        self.assertEqual(self.packet["body"].count("?"), 1)
        self.assertEqual(self.packet["independent_policy_questions_combined"], 1)

    def test_it_does_not_ask_about_commercial_use_again(self):
        self.assertFalse(self.packet["asks_about_commercial_use"])
        after_acknowledgement = self.packet["body"].lower().split("commercial-use point")[-1]
        self.assertNotIn("commercial use", after_acknowledgement)

    def test_the_body_names_the_question_it_is_asking(self):
        for token in ("HEAD", "third-party", "do not own or operate"):
            with self.subTest(token=token):
                self.assertIn(token, self.packet["body"])

    def test_it_was_not_broadened(self):
        body = self.packet["body"].lower()
        for term in gate().BROADENING_TERMS:
            with self.subTest(term=term):
                self.assertNotIn(term.lower(), body)
        self.assertFalse(self.packet["legal_interpretation_added"])
        self.assertFalse(self.packet["examples_added"])

    def test_the_wording_is_the_operators_and_only_the_wrapping_is_not(self):
        self.assertTrue(self.packet["body_differs_from_the_supplied_text_only_by_line_wrapping"])
        self.assertEqual(
            " ".join(self.packet["body"].split()),
            " ".join(self.packet["body_as_supplied_by_the_operator"].split()),
        )
        self.assertNotEqual(self.packet["body"], self.packet["body_as_supplied_by_the_operator"])


class TestTheDiscriminatorIsFrozenBeforeDispatch(unittest.TestCase):
    def setUp(self):
        self.discriminator = load(PACKET)["expected_answer_discriminator"]

    def test_all_three_resolving_answers_are_available(self):
        closing = self.discriminator["closes_r2_b_only_if_the_reply_explicitly_establishes_one_of"]
        self.assertEqual(tuple(closing), gate().RESOLVING_ANSWERS)
        for answer, text in closing.items():
            with self.subTest(answer=answer):
                self.assertTrue(text.strip())

    def test_a_prohibition_is_a_resolving_answer_too(self):
        """A discriminator that only admits a yes is a wish: it would make a refusal
        unrecordable and leave R2-B open however the provider answered."""
        closing = self.discriminator["closes_r2_b_only_if_the_reply_explicitly_establishes_one_of"]
        self.assertIn("NOT_PERMITTED", closing)

    def test_it_requires_an_explicit_target_scope_answer(self):
        self.assertTrue(
            self.discriminator["the_answer_must_address_third_party_target_scope_explicitly"]
        )

    def test_every_route_this_arc_already_refused_is_named(self):
        for route in gate().NON_CLOSING:
            with self.subTest(route=route):
                self.assertIn(route, self.discriminator["does_not_close_r2_b"])

    def test_the_presupposition_route_says_why_it_is_listed(self):
        self.assertIn("presupposition", self.discriminator["why_presupposition_is_listed"])


class TestNothingWasAuthorisedSentOrMoved(unittest.TestCase):
    def setUp(self):
        self.packet = load(PACKET)

    def test_the_packet_records_no_approval_and_no_send(self):
        self.assertEqual(self.packet["send_status"], "NOT_AUTHORIZED")
        self.assertFalse(self.packet["operator_approval_recorded"])
        self.assertFalse(self.packet["sent"])
        self.assertFalse(self.packet["execution_record_created"])
        self.assertEqual(self.packet["maximum_outward_replies"], 1)

    def test_no_outward_action_was_performed(self):
        actions = self.packet["outward_actions_performed_by_this_mission"]
        for counter in gate().OUTWARD_COUNTERS:
            with self.subTest(counter=counter):
                self.assertEqual(actions[counter], 0)

    def test_authority_stays_a_separate_gate(self):
        authority = self.packet["authority_of_the_prior_reply"]
        self.assertEqual(authority["sender_identity"], "NOT_ESTABLISHED")
        self.assertFalse(authority["claimed_by_this_mission"])
        self.assertFalse(authority["does_it_block_preparing_this_packet"])
        self.assertTrue(
            authority["semantic_responsiveness_and_provider_authority_are_separate_gates"]
        )

    def test_r2_b_and_the_qualification_are_untouched(self):
        self.assertEqual(load(THIRD_PARTY)["verdict"], "THIRD_PARTY_TARGET_SCOPE_UNRESOLVED")
        qualification = load(QUALIFICATION)
        gates = {g["dimension"]: g["status"] for g in qualification["gates"]}
        self.assertEqual(gates["C9_RIGHTS_FEASIBILITY"], "PARTIAL")
        self.assertEqual(
            qualification["tally"], {"PASS": 11, "PARTIAL": 1, "FAIL": 0, "UNKNOWN": 0}
        )
        self.assertEqual(qualification["verdict"], "COUNTERPART_UNRESOLVED")

    def test_the_frozen_reply_is_unchanged_and_still_unattributed(self):
        reply = load(FROZEN_REPLY)
        self.assertEqual(
            reply["reply"]["body_sha256"],
            hashlib.sha256(reply["reply"]["body"].encode("utf-8")).hexdigest(),
        )
        self.assertFalse(reply["attribution"]["sufficient_for_provider_authority"])


class TestTheGateRefusesTheShortcuts(unittest.TestCase):
    def setUp(self):
        self.gate = gate()
        self.packet = load(PACKET)

    def rehash(self, packet):
        packet["content_sha256"] = self.gate._digest(packet, packet["hash_covers"])
        return packet

    def refused(self, packet, check=None):
        checker = check or self.gate._check_it_asks_one_question
        with self.assertRaises(self.gate.ValidationError):
            checker(packet)

    def test_the_packet_as_committed_passes(self):
        self.gate.validate()

    def test_an_address_in_the_recipient_is_refused(self):
        packet = self.rehash({**copy.deepcopy(self.packet), "recipient": "d@globalping.io"})
        self.refused(packet, self.gate._check_the_thread_is_what_is_bound)

    def test_asking_commercial_use_again_is_refused(self):
        packet = copy.deepcopy(self.packet)
        packet["asks_about_commercial_use"] = True
        self.refused(packet)

    def test_a_second_question_is_refused(self):
        packet = copy.deepcopy(self.packet)
        packet["body"] += " And is commercial use still fine?"
        self.refused(self.rehash(packet))

    def test_broadening_the_body_is_refused(self):
        packet = copy.deepcopy(self.packet)
        packet["body"] += " Or may I scan a range?"
        self.refused(self.rehash(packet))

    def test_a_body_edited_without_rehashing_is_refused(self):
        packet = copy.deepcopy(self.packet)
        packet["body"] += " extra"
        self.refused(packet, self.gate._check_it_answers_to_its_own_hash)

    def test_more_than_one_outward_reply_is_refused(self):
        packet = copy.deepcopy(self.packet)
        packet["maximum_outward_replies"] = 2
        self.refused(packet, self.gate._check_nothing_was_authorised_or_sent)

    def test_recording_an_approval_in_the_packet_is_refused(self):
        packet = copy.deepcopy(self.packet)
        packet["operator_approval_recorded"] = True
        self.refused(packet, self.gate._check_nothing_was_authorised_or_sent)

    def test_claiming_authority_for_the_earlier_reply_is_refused(self):
        packet = copy.deepcopy(self.packet)
        packet["authority_of_the_prior_reply"]["claimed_by_this_mission"] = True
        self.refused(packet, self.gate._check_nothing_was_authorised_or_sent)

    def test_dropping_a_refused_route_from_the_discriminator_is_refused(self):
        for route in self.gate.NON_CLOSING:
            with self.subTest(route=route):
                packet = copy.deepcopy(self.packet)
                packet["expected_answer_discriminator"]["does_not_close_r2_b"] = [
                    r for r in self.gate.NON_CLOSING if r != route
                ]
                self.refused(packet, self.gate._check_the_discriminator_is_frozen_and_strict)

    def test_removing_a_resolving_answer_is_refused(self):
        for answer in self.gate.RESOLVING_ANSWERS:
            with self.subTest(answer=answer):
                packet = copy.deepcopy(self.packet)
                packet["expected_answer_discriminator"][
                    "closes_r2_b_only_if_the_reply_explicitly_establishes_one_of"
                ].pop(answer)
                self.refused(packet, self.gate._check_the_discriminator_is_frozen_and_strict)

    def test_reusing_the_old_question_id_is_refused(self):
        packet = self.rehash({**copy.deepcopy(self.packet), "question_id": "GP-R2-Q1"})
        self.refused(packet, self.gate._check_it_is_a_new_question)

    def test_a_missing_field_is_a_refusal_rather_than_a_crash(self):
        self.assertIn('ValidationError(f"the records do not carry', RENDERER.read_text("utf-8"))


class TestTheRendererAndGovernance(unittest.TestCase):
    def test_the_renderer_cannot_send_or_read_mail(self):
        source = RENDERER.read_text(encoding="utf-8")
        for banned in ("smtplib", "imaplib", "requests", "httpx", "urllib", "subprocess"):
            with self.subTest(module=banned):
                self.assertNotIn(f"import {banned}", source)

    def test_the_page_reports_the_unauthorised_status_and_the_sentinel(self):
        text = PAGE.read_text(encoding="utf-8")
        self.assertIn("Do not edit by hand", text)
        self.assertIn("NOT_AUTHORIZED", text)
        self.assertIn(gate().RECIPIENT_SENTINEL, text)
        self.assertIn("GP-R2-B-Q1", text)

    def test_ci_runs_the_gate(self):
        self.assertIn(RENDERER.name, CI.read_text(encoding="utf-8"))

    def test_the_manifest_lists_the_packet_and_the_renderer(self):
        text = MANIFEST.read_text(encoding="utf-8")
        for path in (PACKET, RENDERER):
            with self.subTest(record=path.name):
                self.assertIn(path.name, text)

    def test_the_report_exists(self):
        self.assertTrue((REPO_ROOT / "docs" / "reports" / "mission-1.76.2-report.md").exists())


if __name__ == "__main__":
    unittest.main()
