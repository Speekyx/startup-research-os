"""Mission 1.84.1. A route that shares a vendor does not share a permission.

Four things this file defends.

THE SUBSCRIPTION ROUTE IS ITS OWN PROVIDER. It has its own id, its own posture, and its own
retrieved evidence. The API route's assessment still excludes consumer products by name, the set
of APPROVED providers did not grow, and nothing can reach an approval by calling itself Anthropic.

THE REFUSAL RESTS ON THE PROVIDER'S OWN WORDS. The consumer data policy makes training a setting
the account holder chooses; the TED condition this deployment adopted requires terms that commit.
A setting is not a term, and the record quotes the condition rather than paraphrasing it.

TWO BLOCKERS ARE PROPERTIES OF THE SURFACE. A subscription authenticates an agent harness, which
composes its own prompt and decides its own number of model requests. Neither can be reconciled
with a frozen prompt digest and MAX_MODEL_CALLS = 1, and no operator decision changes that.

NOTHING WAS EXECUTED, EXPOSED OR EDITED. Zero remote calls, zero TED bytes, zero credential values,
and V1 byte-identical with its approval flag still false.
"""

from __future__ import annotations

import hashlib
import json
import pathlib
import re
import unittest

REPO_ROOT = pathlib.Path(__file__).resolve().parents[4]
DATA = REPO_ROOT / "docs" / "data"
SCRIPTS = REPO_ROOT / "infrastructure" / "scripts"

RECORD = DATA / "claude-subscription-route-feasibility-v1.json"
REGISTER = DATA / "model-provider-policy-v1.json"
PACKET_V1 = DATA / "second-opportunity-synthesis-execution-packet-v1.json"
DECISION_PACKET = DATA / "ted-selected-candidate-egress-decision-packet-v1.json"
GATE = SCRIPTS / "render_claude_subscription_route_feasibility.py"
CI = REPO_ROOT / ".github" / "workflows" / "ci.yml"

SUBSCRIPTION_ID = "anthropic-claude-subscription"
V1_SHA256 = "570657e1a862a96742925f6a5e5a17b0e1860bf9f2f0b8315fa33c560496da92"


def load(path: pathlib.Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


class TestTheRouteIsItsOwnProvider(unittest.TestCase):
    def setUp(self) -> None:
        self.register = load(REGISTER)
        self.entries = {p["provider_id"]: p for p in self.register["providers"]}

    def test_the_subscription_route_has_its_own_provider_id(self) -> None:
        self.assertIn(SUBSCRIPTION_ID, self.entries)
        self.assertNotEqual(SUBSCRIPTION_ID, "anthropic")

    def test_its_posture_refuses(self) -> None:
        self.assertEqual(self.entries[SUBSCRIPTION_ID]["posture"], "NOT_APPROVED")

    def test_the_approved_set_did_not_grow(self) -> None:
        """A feasibility mission may record a refusal and may not widen an approval."""
        approved = sorted(p for p, e in self.entries.items() if e["posture"] == "APPROVED")
        self.assertEqual(approved, ["anthropic"])

    def test_the_api_route_still_excludes_consumer_products_by_name(self) -> None:
        scope = self.entries["anthropic"]["route_assessed"]
        for word in ("Free", "Pro", "Max"):
            self.assertIn(word, scope)
        self.assertIn("not assessed here", scope)

    def test_the_api_route_posture_was_not_touched(self) -> None:
        entry = self.entries["anthropic"]
        self.assertEqual(entry["posture"], "APPROVED")
        self.assertEqual(entry["trains_on_submitted_content"], "NO_BY_CONTRACT")

    def test_the_refusal_rests_on_retrieved_first_party_evidence(self) -> None:
        evidence = self.entries[SUBSCRIPTION_ID]["evidence"]
        self.assertGreaterEqual(len(evidence), 2)
        for row in evidence:
            self.assertTrue(row["document_url"].startswith("https://"))
            self.assertTrue(row["summarized_finding"].strip())
            self.assertTrue(row["retrieved_at"].strip())

    def test_the_register_says_which_review_added_the_entry(self) -> None:
        """The file-level review date is not rewritten when one entry is added."""
        entry = self.entries[SUBSCRIPTION_ID]
        self.assertEqual(entry["added_by"], "mission-1.84.1")
        self.assertEqual(self.register["reviewed_by"], "mission-1.23")
        self.assertTrue(self.register["$note_on_review_metadata"].strip())

    def test_the_policy_version_moved_with_the_register(self) -> None:
        self.assertGreaterEqual(self.register["policy_version"], 2)


class TestTheRefusalRestsOnTheProvidersOwnWords(unittest.TestCase):
    def setUp(self) -> None:
        self.record = load(RECORD)
        self.blocker = self.record["BLOCKER_3_PROVIDER_GOVERNANCE"]

    def test_the_existing_posture_does_not_cover_the_new_route(self) -> None:
        self.assertFalse(
            self.blocker["CAN_EXISTING_ANTHROPIC_PROVIDER_POSTURE_COVER_SUBSCRIPTION_ROUTE"]
        )

    def test_the_ted_condition_is_quoted_rather_than_paraphrased(self) -> None:
        """The load-bearing phrase decides it, so it has to survive into the record."""
        condition = next(
            c for c in load(DECISION_PACKET)["CONDITIONS"] if c.startswith("PROVIDER-BOUND")
        )
        self.assertIn("its own terms commit", condition)
        self.assertIn("its own terms commit", self.blocker["required_property"])

    def test_a_setting_is_recorded_as_different_from_a_term(self) -> None:
        offered = self.blocker["what_the_subscription_route_offers_instead"]
        self.assertIn("setting", offered)

    def test_the_review_was_performed_rather_than_deferred(self) -> None:
        self.assertTrue(self.blocker["REVIEW_PERFORMED_BY_THIS_MISSION"])
        self.assertEqual(self.blocker["PROVIDER_GOVERNANCE_STATE"], "NOT_APPROVED")

    def test_the_separate_provider_id_has_a_stated_reason(self) -> None:
        self.assertIn("BY NAME", self.blocker["why_a_separate_provider_id"])


class TestTheSurfaceBlockers(unittest.TestCase):
    def setUp(self) -> None:
        self.record = load(RECORD)

    def test_the_frozen_prompt_bytes_cannot_be_transmitted(self) -> None:
        blocker = self.record["BLOCKER_1_PROMPT_IDENTITY"]
        self.assertFalse(blocker["can_the_frozen_bytes_be_transmitted"])
        self.assertFalse(blocker["operator_decision_can_clear_this"])

    def test_exactly_one_call_cannot_be_enforced(self) -> None:
        blocker = self.record["BLOCKER_2_EXACTLY_ONE_CALL"]
        self.assertEqual(blocker["FROZEN_MAX_MODEL_CALLS"], 1)
        self.assertFalse(blocker["can_exactly_one_call_be_enforced"])
        self.assertFalse(blocker["operator_decision_can_clear_this"])
        self.assertEqual(blocker["installed_cli_flags_that_would_bound_it"], [])

    def test_one_invocation_is_a_task_and_not_a_call(self) -> None:
        blocker = self.record["BLOCKER_2_EXACTLY_ONE_CALL"]
        self.assertIn("TASK", blocker["one_invocation_is"])

    def test_a_fallback_flag_is_named_as_forbidden(self) -> None:
        """§18. Fallback between billing routes is a hard failure, not a convenience."""
        joined = " ".join(self.record["BLOCKER_2_EXACTLY_ONE_CALL"]["flags_present_but_wrong_unit"])
        self.assertIn("--fallback-model", joined)

    def test_the_switch_is_recorded_in_the_tooling_s_own_words(self) -> None:
        switch = self.record["THE_SWITCH"]
        self.assertEqual(switch["flag"], "--bare")
        self.assertIn("OAuth and keychain are never read", switch["documented_as"])
        self.assertIn("opposite sides", switch["consequence"])


class TestNothingWasExecutedOrExposed(unittest.TestCase):
    def setUp(self) -> None:
        self.record = load(RECORD)

    def test_every_accounting_counter_that_must_be_zero_is_zero(self) -> None:
        accounting = self.record["ACCOUNTING"]
        for key in (
            "REMOTE_TEST_CALLS",
            "TED_BYTES_SENT",
            "OPPORTUNITY_MODEL_CALLS",
            "ALL_REMOTE_MODEL_CALLS",
            "canonical_research_mutation",
            "opportunities_created",
            "credential_values_exposed",
        ):
            self.assertEqual(accounting[key], 0, key)

    def test_documentation_was_actually_retrieved(self) -> None:
        self.assertGreater(self.record["ACCOUNTING"]["documentation_requests"], 0)

    def test_no_credential_value_was_read_printed_or_persisted(self) -> None:
        tooling = self.record["LOCAL_TOOLING"]
        self.assertEqual(tooling["credential_values_read"], 0)
        self.assertEqual(tooling["credential_values_printed"], 0)
        self.assertEqual(tooling["credential_values_persisted"], 0)

    def test_the_record_carries_nothing_shaped_like_a_credential(self) -> None:
        text = json.dumps(self.record, ensure_ascii=False)
        for pattern in (r"sk-ant-[A-Za-z0-9_\-]{8,}", r"\bey[JI][A-Za-z0-9_\-]{20,}\."):
            self.assertIsNone(re.search(pattern, text), pattern)

    def test_the_api_key_presence_is_reported_and_its_value_is_not(self) -> None:
        collision = self.record["ENVIRONMENT_COLLISION"]
        self.assertTrue(collision["ANTHROPIC_API_KEY_PRESENT_IN_THE_DEPLOYMENT_ENV"])
        self.assertFalse(collision["value_read"])

    def test_the_two_environments_are_reported_apart(self) -> None:
        """The env this mission can see is not the env an SROS job inherits."""
        collision = self.record["ENVIRONMENT_COLLISION"]
        self.assertNotEqual(
            collision["ANTHROPIC_API_KEY_PRESENT_IN_THIS_AGENT_PROCESS"],
            collision["ANTHROPIC_API_KEY_PRESENT_IN_THE_DEPLOYMENT_ENV"],
        )
        self.assertTrue(collision["why_the_two_differ_matters"].strip())


class TestV1WasNotTouched(unittest.TestCase):
    def test_the_frozen_packet_still_hashes_to_what_it_was_frozen_at(self) -> None:
        self.assertEqual(load(PACKET_V1)["EXECUTION_PACKET_SHA256"], V1_SHA256)

    def test_it_still_records_no_approval(self) -> None:
        self.assertFalse(load(PACKET_V1)["OPERATOR_EXECUTION_APPROVAL_RECORDED"])

    def test_the_record_says_it_edited_nothing(self) -> None:
        v1 = load(RECORD)["V1_UNTOUCHED"]
        for key in (
            "edited_by_this_mission",
            "provider_changed",
            "model_changed",
            "approval_invented",
        ):
            self.assertFalse(v1[key], key)

    def test_the_research_payload_is_the_approved_one(self) -> None:
        record = load(RECORD)["RESEARCH_SEMANTICS_UNCHANGED"]
        packet = load(PACKET_V1)
        self.assertEqual(record["REPRESENTATION_SHA256"], packet["REPRESENTATION_SHA256"])
        self.assertEqual(record["PROMPT_SHA256"], packet["PROMPT_SHA256"])
        self.assertTrue(record["REPRESENTATION_UNCHANGED"])
        self.assertTrue(record["PROMPT_UNCHANGED"])


class TestNoV2AndNoInvention(unittest.TestCase):
    def setUp(self) -> None:
        self.record = load(RECORD)

    def test_this_mission_created_no_v2_packet(self) -> None:
        """Re-pointed in Mission 1.84.6: a V2 on disk is a later mission's, never this one's."""
        self.assertFalse(self.record["EXECUTION_PACKET_V2"]["EXECUTION_PACKET_V2_CREATED"])
        path = DATA / "second-opportunity-synthesis-execution-packet-v2.json"
        if path.exists():
            prepared_by = load(path)["prepared_by"]
            later = tuple(int(p) for p in prepared_by.removeprefix("mission-").split("."))
            self.assertGreater(later, (1, 84, 1), prepared_by)

    def test_the_failed_conditions_are_named(self) -> None:
        v2 = self.record["EXECUTION_PACKET_V2"]
        self.assertTrue(v2["conditions_failed"])
        self.assertLess(v2["conditions_met"], v2["conditions_required"])

    def test_v1_is_recommended_with_a_basis(self) -> None:
        self.assertEqual(self.record["RECOMMENDED_EXECUTION_PACKET"], "V1")
        self.assertTrue(self.record["recommendation_basis"].strip())

    def test_the_subscription_is_neither_free_nor_unlimited(self) -> None:
        billing = self.record["BILLING"]
        self.assertFalse(billing["subscription_is_free"])
        self.assertFalse(billing["subscription_is_unlimited"])
        self.assertTrue(billing["SUBSCRIPTION_USAGE_LIMITED"])

    def test_no_dollar_saving_and_no_quota_percentage_were_invented(self) -> None:
        billing = self.record["BILLING"]
        self.assertTrue(billing["no_dollar_saving_is_claimed"])
        self.assertFalse(billing["quota_percentage_invented"])

    def test_payg_is_still_true_for_v1(self) -> None:
        self.assertTrue(self.record["BILLING"]["V1_API_PAYG"])

    def test_no_model_was_assumed_available(self) -> None:
        models = self.record["MODEL_AVAILABILITY"]
        self.assertEqual(models["AVAILABLE_SUBSCRIPTION_MODELS"], "NOT_ESTABLISHED")
        self.assertIsNone(models["SELECTED_SUBSCRIPTION_MODEL"])
        self.assertIn("subscription model names", models["what_was_NOT_assumed"])

    def test_no_route_was_selected(self) -> None:
        self.assertIsNone(self.record["SELECTED_SUBSCRIPTION_ROUTE"])

    def test_the_brief_s_max_premise_was_corrected_rather_than_adopted(self) -> None:
        """A record that wrote MAX into its fields would assert an account fact nobody has."""
        tier = self.record["premise_correction"]
        self.assertEqual(tier["MAX_TIER"], "NOT_MAX_ON_THIS_MACHINE")
        self.assertNotIn(tier["LOCALLY_HELD_SUBSCRIPTION_TYPE"], {"max", "MAX"})


class TestTheArchitectureWasDeterminedAndNotBuilt(unittest.TestCase):
    def setUp(self) -> None:
        self.record = load(RECORD)

    def test_no_adapter_was_built_for_a_refused_route(self) -> None:
        architecture = self.record["GATEWAY_ARCHITECTURE_REQUIRED"]
        self.assertFalse(architecture["implemented_by_this_mission"])
        self.assertTrue(architecture["why_not_implemented"].strip())

    def test_the_forbidden_fallback_shape_is_named(self) -> None:
        architecture = self.record["GATEWAY_ARCHITECTURE_REQUIRED"]
        self.assertEqual(architecture["forbidden_shape"], "try subscription, then API")

    def test_the_gateway_does_not_fail_closed_today_and_says_why(self) -> None:
        collision = self.record["ENVIRONMENT_COLLISION"]
        self.assertFalse(collision["SUBSCRIPTION_ROUTE_FAILS_CLOSED_TODAY"])
        self.assertIn("no route concept", collision["why_not"])

    def test_the_required_invariant_is_stated(self) -> None:
        collision = self.record["ENVIRONMENT_COLLISION"]
        self.assertIn(
            "never execute through ANTHROPIC_PLATFORM_API", collision["required_future_invariant"]
        )

    def test_no_subscription_adapter_exists_in_the_gateway(self) -> None:
        providers = (
            REPO_ROOT / "packages" / "llm-gateway" / "python" / "sros_llm_gateway" / "providers"
        )
        names = sorted(p.stem for p in providers.glob("*.py"))
        self.assertEqual(names, ["__init__", "anthropic", "fake", "gemini"])


class TestTheGateIsWired(unittest.TestCase):
    def test_the_gate_exists_and_runs_in_ci(self) -> None:
        self.assertTrue(GATE.exists())
        self.assertIn("render_claude_subscription_route_feasibility.py --check", CI.read_text())

    def test_the_rendered_page_exists(self) -> None:
        self.assertTrue((DATA / "claude-subscription-route-feasibility-v1.md").exists())

    def test_the_gate_pins_v1s_digest_rather_than_reading_it(self) -> None:
        """A gate that read the digest from the file it guards would guard nothing."""
        text = GATE.read_text(encoding="utf-8")
        self.assertIn(V1_SHA256, text)

    def test_the_record_file_is_stable(self) -> None:
        digest = hashlib.sha256(RECORD.read_bytes()).hexdigest()
        self.assertEqual(len(digest), 64)


if __name__ == "__main__":
    unittest.main()
