"""Mission 1.65. Two enquiries, two envelopes, and one approval that can be given.

Three things are newly testable here.

The first is the circularity the envelope hash had to survive. An envelope hash
is an approval handle, so it must be WRITTEN INTO the envelope; and a hash
computed over the whole envelope would change the moment it was recorded.
Mission 1.56 solved the same shape for a frozen manifest by keeping the hash
outside the bytes it names. An envelope cannot do that, because the operator
approves the envelope itself, so the digest is taken over a named set of BINDING
fields that excludes the hash and the approval string. The test recomputes it
from the file as stored and asserts the recorded value.

The second is that the digest binds the ACTION rather than the document. An
approval of text is not an approval of a channel (Mission 1.64), so changing the
recipient, the channel or the sender must move the hash, and changing when the
envelope was written must not.

The third is negative and is the whole mission: nothing was sent. One envelope is
complete and awaiting an operator; the other names nobody, carries no hash, and
is therefore not approvable at all.

Nothing here is persisted, no measurement was retrieved, and no enquiry left the
repository.
"""

from __future__ import annotations

import hashlib
import json
import pathlib
import re
import unittest

REPO_ROOT = pathlib.Path(__file__).resolve().parents[4]
DATA = REPO_ROOT / "docs" / "data"

BASELINE = DATA / "mission-1.65-baseline-v1.json"
ENQUIRY = DATA / "onyphe-technical-methodology-enquiry-v1.json"
CONTRACT = DATA / "outbound-dispatch-envelope-contract-v1.json"
NETLAS_ENV = DATA / "netlas-dispatch-envelope-v1.json"
ONYPHE_ENV = DATA / "onyphe-dispatch-envelope-v1.json"
READINESS = DATA / "dual-enquiry-readiness-v1.json"

NETLAS_ENQUIRY_MD = DATA / "anchor-technical-lineage-enquiry-v1.md"
ONYPHE_ENQUIRY_MD = DATA / "onyphe-technical-methodology-enquiry-v1.md"
PACKET_MD = DATA / "onyphe-enquiry-dispatch-packet-v1.md"

NETLAS_APPROVED_SHA256 = "310acf288244453cd0a928197386cbf8311ded278e4dcdd22b70412807a049c4"

ALL_RECORDS = (BASELINE, ENQUIRY, CONTRACT, NETLAS_ENV, ONYPHE_ENV, READINESS)

# Independently restated here rather than imported, so a change to the renderer's
# canonicalisation has to be made in two places by somebody who meant it.
BINDING_FIELDS = (
    "enquiry_document_id",
    "enquiry_content_sha256",
    "recipient_address",
    "outbound_channel",
    "sender_identity",
    "subject",
    "content_version",
)


def _load(path: pathlib.Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _prose(node: object) -> list[str]:
    out: list[str] = []
    if isinstance(node, dict):
        for key, value in node.items():
            if key.startswith("$"):
                continue
            out.extend(_prose(value))
    elif isinstance(node, list):
        for item in node:
            out.extend(_prose(item))
    elif isinstance(node, str):
        out.append(node)
    return out


def _envelope_digest(envelope: dict, content_sha: str) -> str:
    binding = {f: envelope.get(f) for f in BINDING_FIELDS}
    binding["enquiry_content_sha256"] = content_sha
    blob = json.dumps(binding, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    return hashlib.sha256(blob.encode("utf-8")).hexdigest()


class TestTheApprovedNetlasBodyIsUntouched(unittest.TestCase):
    """An approval names a hash. If the bytes moved, the approval names nothing."""

    def test_the_approved_body_still_hashes_to_the_approved_value(self) -> None:
        live = hashlib.sha256(NETLAS_ENQUIRY_MD.read_bytes()).hexdigest()
        self.assertEqual(live, NETLAS_APPROVED_SHA256)

    def test_the_netlas_envelope_names_the_approved_hash_and_no_other(self) -> None:
        self.assertEqual(_load(NETLAS_ENV)["enquiry_content_sha256"], NETLAS_APPROVED_SHA256)

    def test_no_recipient_was_written_into_the_approved_body(self) -> None:
        # Mission 1.61 kept the recipient outside the hashed document precisely so
        # that finding an address three missions later would not void the approval.
        body = NETLAS_ENQUIRY_MD.read_text(encoding="utf-8")
        self.assertNotIn("@", body.split("## Provenance")[0].replace("@1.", ""))


class TestContentApprovalIsNotDispatchApproval(unittest.TestCase):
    """The rule this mission freezes, checked on the record that carries it."""

    def test_the_carried_approval_grants_content_and_nothing_else(self) -> None:
        carried = _load(BASELINE)["content_approval_carried_forward"]
        self.assertIs(carried["CONTENT_APPROVED"], True)
        for name in ("RECIPIENT_APPROVED", "CHANNEL_APPROVED", "SEND_NOW"):
            self.assertIs(carried[name], False, name)

    def test_the_contract_names_the_rule_and_creates_no_migration(self) -> None:
        rule = _load(CONTRACT)["the_rule_this_freezes"]
        self.assertEqual(rule["name"], "CONTENT_APPROVAL_IS_NOT_DISPATCH_APPROVAL")
        self.assertIs(rule["no_migration"], True)
        self.assertIs(rule["no_global_approval_subsystem"], True)

    def test_the_three_gates_are_three(self) -> None:
        gates = _load(CONTRACT)["three_gates_that_stay_separate"]
        named = {k for k in gates if not k.startswith("$")}
        self.assertEqual(
            named,
            {"CONTENT_APPROVAL", "RECIPIENT_ESTABLISHMENT", "CHANNEL_AUTHORIZATION"},
        )


class TestTheEnvelopeHashSurvivesBeingRecorded(unittest.TestCase):
    """The circularity check. Recording the hash must not move the hash."""

    def setUp(self) -> None:
        self.envelope = _load(ONYPHE_ENV)
        self.content_sha = hashlib.sha256(ONYPHE_ENQUIRY_MD.read_bytes()).hexdigest()

    def test_the_recorded_content_hash_matches_the_rendered_enquiry(self) -> None:
        self.assertEqual(self.envelope["enquiry_content_sha256"], self.content_sha)

    def test_the_recorded_envelope_hash_recomputes_from_the_file_as_stored(self) -> None:
        # The file on disk already carries the hash. If the digest were taken over
        # the whole envelope it could not equal what is written inside it.
        self.assertEqual(
            self.envelope["envelope_sha256"],
            _envelope_digest(self.envelope, self.content_sha),
        )

    def test_neither_the_hash_nor_the_approval_string_is_a_binding_field(self) -> None:
        self.assertNotIn("envelope_sha256", BINDING_FIELDS)
        self.assertNotIn("approval_string", BINDING_FIELDS)
        declared = _load(CONTRACT)["envelope_hash"]
        self.assertNotIn("envelope_sha256", declared["binding_fields"])

    def test_no_placeholder_survives_in_the_envelope(self) -> None:
        blob = ONYPHE_ENV.read_text(encoding="utf-8")
        self.assertNotIn("PLACEHOLDER_COMPUTED_BY_RENDERER", blob)


class TestTheHashBindsTheActionRatherThanTheDocument(unittest.TestCase):
    """An approval of text is not an approval of a channel."""

    def setUp(self) -> None:
        self.envelope = _load(ONYPHE_ENV)
        self.content_sha = self.envelope["enquiry_content_sha256"]
        self.actual = _envelope_digest(self.envelope, self.content_sha)

    def _moved(self, field: str, value: object) -> bool:
        altered = dict(self.envelope)
        altered[field] = value
        return _envelope_digest(altered, self.content_sha) != self.actual

    def test_changing_the_recipient_moves_the_hash(self) -> None:
        self.assertTrue(self._moved("recipient_address", "someone.else@example.invalid"))

    def test_changing_the_channel_moves_the_hash(self) -> None:
        self.assertTrue(self._moved("outbound_channel", "AUTHORIZED_CONNECTOR"))

    def test_changing_the_sender_moves_the_hash(self) -> None:
        self.assertTrue(self._moved("sender_identity", "a-named-mailbox"))

    def test_changing_the_subject_moves_the_hash(self) -> None:
        self.assertTrue(self._moved("subject", "Something else entirely"))

    def test_changing_the_content_hash_moves_the_envelope_hash(self) -> None:
        other = _envelope_digest(self.envelope, "0" * 64)
        self.assertNotEqual(other, self.actual)

    def test_changing_when_it_was_recorded_does_not_move_the_hash(self) -> None:
        # Provenance about the action is not part of the action.
        self.assertFalse(self._moved("recorded_at", "1999-01-01"))

    def test_changing_why_the_connector_was_refused_does_not_move_the_hash(self) -> None:
        self.assertFalse(self._moved("why_the_connector_was_not_selected", "reworded"))


class TestAnEnvelopeWithNoRecipientIsNotApprovable(unittest.TestCase):
    """A hash is an approval handle, so an incomplete action has none."""

    def setUp(self) -> None:
        self.envelope = _load(NETLAS_ENV)

    def test_the_netlas_envelope_names_nobody(self) -> None:
        self.assertEqual(self.envelope["state"], "INCOMPLETE_RECIPIENT")
        self.assertIsNone(self.envelope["recipient_address"])

    def test_it_carries_no_hash_no_approval_string_and_is_not_approvable(self) -> None:
        self.assertIsNone(self.envelope["envelope_sha256"])
        self.assertIsNone(self.envelope["approval_string"])
        self.assertIs(self.envelope["approvable"], False)

    def test_no_packet_was_generated_for_it(self) -> None:
        self.assertIs(self.envelope["packet_generated"], False)
        self.assertFalse((DATA / "netlas-enquiry-dispatch-packet-v1.md").exists())

    def test_no_mailbox_was_invented_inferred_or_decoded(self) -> None:
        for flag in ("address_invented", "address_inferred", "obfuscation_decoded"):
            self.assertIs(self.envelope[flag], False, flag)
        self.assertIs(self.envelope["conventional_mailboxes_refused"], True)


class TestRecipientProvenanceRatherThanSpelling(unittest.TestCase):
    """A retrieved mailbox may look conventional; a guessed one may not."""

    def setUp(self) -> None:
        self.prov = _load(ONYPHE_ENV)["recipient_provenance"]

    def test_it_was_read_off_first_party_pages(self) -> None:
        self.assertEqual(self.prov["how_established"], "RETRIEVED_FROM_FIRST_PARTY_PAGE")
        self.assertGreaterEqual(len(self.prov["pages"]), 2)
        for page in self.prov["pages"]:
            self.assertTrue(page["url"].startswith("https://"))
            self.assertTrue(page["rendered_as"].strip())

    def test_nothing_was_invented_inferred_or_decoded(self) -> None:
        for flag in ("address_invented", "address_inferred", "obfuscation_decoded"):
            self.assertIs(self.prov[flag], False, flag)

    def test_the_record_says_why_provenance_rather_than_spelling_decides(self) -> None:
        # The local part is a conventional word, and Mission 1.64's validator lists
        # exactly that string among the mailbox forms it refuses. That rule forbids
        # INFERRING a mailbox, and this one was read. A record that did not say so
        # would look like the rule being quietly dropped.
        self.assertTrue(self.prov["the_distinction_that_matters_here"].strip())

    def test_a_general_contact_route_is_not_claimed_as_a_technical_channel(self) -> None:
        self.assertTrue(self.prov["what_it_is_not"].strip())


class TestTheAddressesThatWereNotChosen(unittest.TestCase):
    """A demo address seen and passed over is a decision, not an omission."""

    def setUp(self) -> None:
        self.envelope = _load(ONYPHE_ENV)

    def test_every_excluded_address_says_why(self) -> None:
        excluded = self.envelope["addresses_seen_and_excluded"]
        self.assertGreaterEqual(len(excluded), 3)
        for item in excluded:
            self.assertTrue(item["purpose_as_printed"].strip())
            self.assertTrue(item["excluded_because"].strip())

    def test_the_demo_address_is_excluded_because_a_trial_is_a_trial(self) -> None:
        reasons = " ".join(
            i["excluded_because"] for i in self.envelope["addresses_seen_and_excluded"]
        ).lower()
        self.assertIn("trial", reasons)


class TestTheChannelWasBoundRatherThanAssumed(unittest.TestCase):
    """A connector present in the runtime is not an authorisation to use it."""

    def setUp(self) -> None:
        self.envelope = _load(ONYPHE_ENV)

    def test_the_channel_is_a_person_sending_it(self) -> None:
        self.assertEqual(self.envelope["outbound_channel"], "OPERATOR_MANUAL_SEND")

    def test_the_connector_is_available_and_not_authorized(self) -> None:
        self.assertEqual(self.envelope["connector_state"], "AVAILABLE_NOT_AUTHORIZED")
        self.assertTrue(self.envelope["why_the_connector_was_not_selected"].strip())

    def test_a_placeholder_sender_states_what_it_costs(self) -> None:
        self.assertIs(self.envelope["sender_identity_is_a_placeholder"], True)
        self.assertTrue(self.envelope["its_cost_stated"].strip())
        self.assertTrue(self.envelope["how_to_pin_the_fourth"].strip())

    def test_the_contract_says_a_connector_never_grants_its_own_authorisation(
        self,
    ) -> None:
        never = " ".join(
            _load(CONTRACT)["three_gates_that_stay_separate"]["CHANNEL_AUTHORIZATION"][
                "never_granted_by"
            ]
        ).lower()
        self.assertIn("connector", never)


class TestTheApprovalStringIsExact(unittest.TestCase):
    """One string, naming one hash, authorising one send."""

    def test_the_string_is_the_frozen_form_over_the_recorded_hash(self) -> None:
        envelope = _load(ONYPHE_ENV)
        self.assertEqual(
            envelope["approval_string"],
            f"APPROVE MISSION 1.65 DISPATCH {envelope['envelope_sha256']}",
        )

    def test_the_contract_fixes_that_form(self) -> None:
        form = _load(CONTRACT)["envelope_hash"]["approval_string_form"]
        self.assertIn("APPROVE MISSION 1.65 DISPATCH", form)

    def test_no_approval_has_been_recorded(self) -> None:
        self.assertIs(_load(ONYPHE_ENV)["approval_recorded"], False)


class TestThePacketIsGeneratedFromTheFrozenEnquiry(unittest.TestCase):
    """A packet retyped from the enquiry can drift from the document it names."""

    def setUp(self) -> None:
        self.enquiry = _load(ENQUIRY)
        self.packet = PACKET_MD.read_text(encoding="utf-8")

    def test_every_frozen_question_appears_verbatim(self) -> None:
        for question in self.enquiry["questions"]:
            self.assertIn(question["question"], self.packet)

    def test_the_preamble_and_closing_appear_verbatim(self) -> None:
        self.assertIn(self.enquiry["preamble"], self.packet)
        self.assertIn(self.enquiry["closing"], self.packet)

    def test_the_packet_names_the_recipient_and_the_two_hashes(self) -> None:
        envelope = _load(ONYPHE_ENV)
        self.assertIn(envelope["recipient_address"], self.packet)
        self.assertIn(envelope["enquiry_content_sha256"], self.packet)
        self.assertIn(envelope["envelope_sha256"], self.packet)


class TestTheFrozenEnquiryItself(unittest.TestCase):
    """A hash guards the body and says nothing about the fields beside it."""

    def setUp(self) -> None:
        self.enquiry = _load(ENQUIRY)

    def test_it_is_not_marked_sent(self) -> None:
        self.assertEqual(self.enquiry["status"], "AWAITING_OPERATOR_DISPATCH_APPROVAL")
        self.assertIs(self.enquiry["delivery"]["sent"], False)
        self.assertIsNone(self.enquiry["delivery"]["sent_at"])

    def test_its_hash_lives_outside_the_bytes_it_hashes(self) -> None:
        boundary = self.enquiry["content_boundary"]
        self.assertIs(boundary["hash_recorded_here"], False)
        self.assertEqual(boundary["hash_recorded_in"], "docs/data/onyphe-dispatch-envelope-v1.json")
        # And the claim is true of the rendered bytes rather than only asserted.
        self.assertNotIn(
            hashlib.sha256(ONYPHE_ENQUIRY_MD.read_bytes()).hexdigest(),
            ONYPHE_ENQUIRY_MD.read_text(encoding="utf-8"),
        )

    def test_exactly_the_three_residual_questions_and_no_fourth(self) -> None:
        prov = self.enquiry["provenance_of_the_three_questions"]
        self.assertEqual(prov["question_count"], 3)
        self.assertEqual(prov["questions_added_beyond_the_frozen_three"], 0)
        self.assertEqual([q["n"] for q in self.enquiry["questions"]], [1, 2, 3])

    def test_the_sendable_body_asks_for_no_data_access_trial_or_price(self) -> None:
        sendable = [self.enquiry["subject"], self.enquiry["preamble"], self.enquiry["closing"]]
        for q in self.enquiry["questions"]:
            sendable += [q["topic"], q["question"], q["why_we_ask"]]
        body = " ".join(sendable).lower()
        for ask in (
            "how many hosts",
            "provide a count",
            "send us a sample",
            "free trial",
            "trial account",
            "evaluation account",
            "pricing",
            "api key",
            "a demo",
        ):
            self.assertNotIn(ask, body, ask)

    def test_it_does_not_ask_the_provider_to_grade_our_gate(self) -> None:
        body = " ".join(
            [self.enquiry["preamble"], self.enquiry["closing"]]
            + [q["question"] for q in self.enquiry["questions"]]
        ).lower()
        self.assertNotIn("observation-addressable", body)
        self.assertNotIn("does your api qualify", body)

    def test_the_already_answered_truncation_is_stated_as_known(self) -> None:
        q3 = next(q for q in self.enquiry["questions"] if q["n"] == 3)
        self.assertIn("truncat", q3["why_we_ask"].lower())
        self.assertEqual(
            self.enquiry["no_data_request_proof"]["already_answered_questions_repeated"], 0
        )


class TestNothingWasSentAndNoGateMoved(unittest.TestCase):
    """The mission stops before dispatch, and asking is not answering."""

    def test_both_envelopes_are_unsent(self) -> None:
        onyphe = _load(ONYPHE_ENV)
        self.assertIs(onyphe["sent"], False)
        self.assertIsNone(onyphe["sent_at"])
        self.assertEqual(onyphe["dispatch_count"], 0)

    def test_every_accounting_counter_is_zero(self) -> None:
        counters = _load(READINESS)["counters"]
        for name in (
            "research_data_requests",
            "measurement_queries",
            "counts_fetched",
            "host_records_fetched",
            "banners_fetched",
            "trials",
            "purchases",
            "outbound_enquiries_sent",
            "model_calls",
            "embeddings",
            "canonical_mutations",
            "sources_registered",
            "governance_reviews_created",
            "apparatus_gates_changed",
        ):
            self.assertEqual(counters[name], 0, name)

    def test_no_apparatus_gate_changed_and_no_pair_work_happened(self) -> None:
        states = _load(READINESS)["apparatus_states_unchanged"]
        for name in ("Netlas", "ONYPHE", "LeakIX", "The Shadowserver Foundation"):
            self.assertIs(states[name]["changed"], False, name)
        self.assertEqual(states["qualified_count"], 0)
        self.assertIs(states["pair_analysis_ready"], False)
        pair = _load(READINESS)["no_pair_work_was_performed"]
        for counter in ("pairs_compared", "pairs_ranked", "pairs_selected"):
            self.assertEqual(pair[counter], 0, counter)

    def test_the_stop_condition_holds_in_every_clause(self) -> None:
        for name, value in _load(READINESS)["stop_condition"].items():
            if name.startswith("$") or name == "awaiting":
                continue
            self.assertIs(value, False, name)


class TestTheReadinessRecordAgreesWithTheEnvelopes(unittest.TestCase):
    """A summary that can disagree with what it summarises is worse than none."""

    def test_each_envelope_row_matches_its_record(self) -> None:
        listed = {e["envelope"]: e for e in _load(READINESS)["envelopes"]}
        for name, record in (
            ("netlas-dispatch-envelope-v1", _load(NETLAS_ENV)),
            ("onyphe-dispatch-envelope-v1", _load(ONYPHE_ENV)),
        ):
            row = listed[name]
            self.assertEqual(row["state"], record["state"], name)
            self.assertEqual(row["recipient_known"], bool(record.get("recipient_address")), name)
            self.assertEqual(row["hashed"], record.get("envelope_sha256") is not None, name)
            self.assertEqual(row["approvable"], record["approvable"], name)

    def test_the_outcome_names_the_state_the_envelopes_are_in(self) -> None:
        readiness = _load(READINESS)
        self.assertEqual(
            readiness["primary_outcome"], "NETLAS_RECIPIENT_PENDING_ONYPHE_ENQUIRY_FROZEN"
        )
        self.assertIsNone(_load(NETLAS_ENV)["recipient_address"])
        self.assertTrue(readiness["primary_outcome_statement"].strip())

    def test_dispatch_readiness_is_not_reported_as_apparatus_progress(self) -> None:
        asymmetry = _load(READINESS)["the_asymmetry_and_why_it_is_not_a_preference"]
        self.assertTrue(asymmetry["not_a_ranking"].strip())
        self.assertTrue(asymmetry["the_temptation_declined"].strip())


class TestNoRecordOverclaims(unittest.TestCase):
    """A methodology question is not a market finding."""

    def test_no_record_uses_commercial_or_adoption_vocabulary(self) -> None:
        for path in ALL_RECORDS:
            for sentence in _prose(_load(path)):
                tokens = set(re.findall(r"[a-z0-9]+", sentence.lower()))
                for term in (
                    "installation",
                    "customer",
                    "subscription",
                    "revenue",
                    "adoption",
                    "demand",
                ):
                    self.assertNotIn(term, tokens, f"{path.name}: {sentence[:80]!r}")


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
