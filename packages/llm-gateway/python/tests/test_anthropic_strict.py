"""Strict tool use: the provider-supported projection and the strict adapter.

Mission 1.84.19. Every case is local: no network, no API key, no bill. The schemas here are small
synthetic ones; the projection of the real output contract is re-derived by CI gate 92, which can
import both packages.
"""

from __future__ import annotations

import ast
import copy
import inspect
import unittest
from typing import Any

from sros_contracts import LlmTier
from sros_llm_gateway import FakeTransport, LlmRequest, RenderedPrompt, UntrustedText
from sros_llm_gateway.providers import anthropic_strict
from sros_llm_gateway.providers.anthropic import (
    STRUCTURED_TOOL_NAME,
    AnthropicProvider,
    AnthropicThinking,
    classify_forced_tool_completion,
)
from sros_llm_gateway.providers.anthropic_strict import (
    ANNOTATION_CARRIED_UNCHANGED,
    ANTHROPIC_STRICT_TOOL_PROFILE_V1,
    LOCAL_ONLY,
    PROVIDER_ENFORCED,
    STRICT_TOOL_FLAG,
    UNSUPPORTED_ARCHITECTURE_BLOCKER,
    AnthropicStrictToolProvider,
    pattern_within_documented_subset,
    project_strict_input_schema,
    strict_incompatibilities,
)
from sros_llm_gateway.types import ProviderInvalidRequestError

PROFILE = ANTHROPIC_STRICT_TOOL_PROFILE_V1
UUID = "^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$"


def contract() -> dict[str, Any]:
    """A closed contract shaped like the synthesis output: every kind of keyword it uses."""
    return {
        "type": "object",
        "additionalProperties": False,
        "required": ["decision", "summary", "ids", "families", "labels", "items"],
        "properties": {
            "decision": {"type": "string", "enum": ["FORM", "INSUFFICIENT"]},
            "summary": {"type": "string", "maxLength": 1500},
            "ids": {
                "type": "array",
                "maxItems": 20,
                "items": {
                    "type": "string",
                    "format": "uuid",
                    "pattern": UUID,
                    "maxLength": 36,
                    "description": "A canonical id.",
                },
            },
            "families": {
                "type": "array",
                "maxItems": 10,
                "items": {"type": "string", "pattern": "^[a-z0-9][a-z0-9._-]{0,127}$"},
            },
            "labels": {
                "type": "array",
                "items": {"type": "string", "minLength": 1, "maxLength": 500},
            },
            "items": {
                "type": "array",
                "maxItems": 24,
                "items": {
                    "type": "object",
                    "additionalProperties": False,
                    "required": ["statement", "classification"],
                    "properties": {
                        "statement": {"type": "string", "maxLength": 300},
                        "classification": {"type": "string", "enum": ["A", "B"]},
                    },
                },
            },
        },
    }


def request(schema: dict[str, Any] | None) -> LlmRequest:
    return LlmRequest(
        tier=LlmTier.STRONG_MODEL,
        task="synthesis",
        prompt_template_id="synthesis",
        prompt_template_version="1.0.0",
        workspace_id="00000000-0000-4000-8000-000000000001",
        correlation_id="corr-strict",
        prompt=RenderedPrompt(
            system_instructions="Return the analysis.",
            trusted_context="",
            task="Analyse.",
            untrusted=(UntrustedText("a supplied statement", "row-1"),),
        ),
        response_schema=schema,
        requires_structured_output=schema is not None,
    )


def strict_provider() -> AnthropicStrictToolProvider:
    return AnthropicStrictToolProvider(
        api_key="k",
        transport=FakeTransport(),
        max_output_tokens=128000,
        thinking=AnthropicThinking.DISABLED,
    )


def rows_for(keyword: str, projection: Any) -> set[str]:
    return {row.disposition for row in projection.rows if row.keyword == keyword}


class TheProjection(unittest.TestCase):
    def setUp(self) -> None:
        self.projection = project_strict_input_schema(contract(), PROFILE)
        self.schema = self.projection.schema

    def test_it_is_ready_with_no_blocker(self) -> None:
        self.assertTrue(self.projection.ready)
        self.assertEqual(self.projection.blockers, ())

    def test_lengths_and_counts_are_not_sent_and_are_recorded_local_only(self) -> None:
        for keyword in ("maxLength", "minLength", "maxItems"):
            self.assertEqual(rows_for(keyword, self.projection), {LOCAL_ONLY}, keyword)
        text = repr(self.schema)
        for keyword in ("maxLength", "minLength", "maxItems"):
            self.assertNotIn(keyword, text)

    def test_what_the_provider_enforces_is_sent_unchanged(self) -> None:
        for keyword in ("type", "required", "additionalProperties", "enum", "format"):
            self.assertEqual(rows_for(keyword, self.projection), {PROVIDER_ENFORCED}, keyword)
        props = self.schema["properties"]
        self.assertEqual(props["decision"]["enum"], ["FORM", "INSUFFICIENT"])
        self.assertEqual(props["ids"]["items"]["format"], "uuid")
        self.assertEqual(
            props["items"]["items"]["properties"]["classification"]["enum"], ["A", "B"]
        )

    def test_a_counted_quantifier_is_not_established_and_a_plain_pattern_is_kept(self) -> None:
        self.assertEqual(rows_for("pattern", self.projection), {LOCAL_ONLY})
        self.assertNotIn("pattern", self.schema["properties"]["ids"]["items"])
        plain = {
            "type": "object",
            "additionalProperties": False,
            "required": ["a"],
            "properties": {"a": {"type": "string", "pattern": "^[a-z]+$"}},
        }
        kept = project_strict_input_schema(plain, PROFILE)
        self.assertEqual(kept.schema["properties"]["a"]["pattern"], "^[a-z]+$")

    def test_every_object_keeps_its_exact_property_and_required_sets_and_stays_closed(self) -> None:
        canonical, projected = contract(), self.schema
        self.assertEqual(list(projected["properties"]), list(canonical["properties"]))
        self.assertEqual(projected["required"], canonical["required"])
        self.assertIs(projected["additionalProperties"], False)
        inner_c = canonical["properties"]["items"]["items"]
        inner_p = projected["properties"]["items"]["items"]
        self.assertEqual(list(inner_p["properties"]), list(inner_c["properties"]))
        self.assertEqual(inner_p["required"], inner_c["required"])
        self.assertIs(inner_p["additionalProperties"], False)

    def test_descriptions_are_carried_unchanged(self) -> None:
        self.assertEqual(rows_for("description", self.projection), {ANNOTATION_CARRIED_UNCHANGED})
        self.assertEqual(
            self.schema["properties"]["ids"]["items"]["description"], "A canonical id."
        )

    def test_it_is_deterministic_and_leaves_its_input_alone(self) -> None:
        source = contract()
        before = copy.deepcopy(source)
        first = project_strict_input_schema(source, PROFILE)
        second = project_strict_input_schema(source, PROFILE)
        self.assertEqual(source, before)
        self.assertEqual(first.schema, second.schema)
        self.assertEqual(first.rows, second.rows)

    def test_it_is_its_own_projection(self) -> None:
        self.assertEqual(strict_incompatibilities(self.schema, PROFILE), [])
        again = project_strict_input_schema(self.schema, PROFILE)
        self.assertEqual(again.schema, self.schema)


class TheBlockers(unittest.TestCase):
    def blocked(self, schema: dict[str, Any]) -> tuple[str, ...]:
        projection = project_strict_input_schema(schema, PROFILE)
        self.assertIsNone(projection.schema)
        self.assertTrue(projection.blockers)
        return projection.blockers

    def test_an_open_object_is_refused(self) -> None:
        schema = contract()
        schema["additionalProperties"] = True
        self.blocked(schema)

    def test_an_object_that_does_not_say_it_is_closed_is_refused(self) -> None:
        schema = contract()
        del schema["properties"]["items"]["items"]["additionalProperties"]
        self.blocked(schema)

    def test_a_keyword_the_profile_does_not_list_is_refused_rather_than_forwarded(self) -> None:
        for keyword, value in (("$ref", "#/$defs/x"), ("anyOf", []), ("uniqueItems", True)):
            schema = contract()
            schema["properties"]["summary"][keyword] = value
            blockers = self.blocked(schema)
            self.assertTrue(any(keyword in b for b in blockers), blockers)
            rows = project_strict_input_schema(schema, PROFILE).rows
            self.assertIn(UNSUPPORTED_ARCHITECTURE_BLOCKER, {r.disposition for r in rows})

    def test_a_complex_enum_member_is_refused(self) -> None:
        schema = contract()
        schema["properties"]["decision"]["enum"] = [{"a": 1}]
        self.blocked(schema)

    def test_the_documented_optional_parameter_limit_holds(self) -> None:
        schema = {
            "type": "object",
            "additionalProperties": False,
            "required": [],
            "properties": {f"p{i}": {"type": "string"} for i in range(25)},
        }
        self.assertTrue(any("optional" in b for b in self.blocked(schema)))


class ThePatternSubset(unittest.TestCase):
    def test_documented_features_are_accepted(self) -> None:
        for pattern in ("^[a-z]+$", "^\\d+-\\w*$", "(ab)+", "^a.b?c*$", "^[\\d\\-]+$"):
            self.assertTrue(pattern_within_documented_subset(pattern)[0], pattern)

    def test_undocumented_or_unestablished_features_are_not(self) -> None:
        for pattern in ("^a{2}$", "^(a|b)$", "^(?=a)b$", "\\bword\\b", "^(a)\\1$", "^[a-z"):
            self.assertFalse(pattern_within_documented_subset(pattern)[0], pattern)


class TheStrictAdapter(unittest.TestCase):
    def setUp(self) -> None:
        self.schema = project_strict_input_schema(contract(), PROFILE).schema

    def test_strict_is_a_top_level_tool_property_and_not_inside_the_input_schema(self) -> None:
        body = strict_provider().build_body(request(self.schema), "claude-sonnet-5")
        tool = body["tools"][0]
        self.assertEqual(list(tool), ["name", "description", STRICT_TOOL_FLAG, "input_schema"])
        self.assertIs(tool[STRICT_TOOL_FLAG], True)
        self.assertNotIn(STRICT_TOOL_FLAG, repr(tool["input_schema"]))
        self.assertEqual(tool["input_schema"], self.schema)

    def test_the_rest_of_the_body_is_the_plain_adapters(self) -> None:
        plain = AnthropicProvider(
            api_key="k",
            transport=FakeTransport(),
            max_output_tokens=128000,
            thinking=AnthropicThinking.DISABLED,
        ).build_body(request(self.schema), "claude-sonnet-5")
        strict = strict_provider().build_body(request(self.schema), "claude-sonnet-5")
        self.assertEqual(len(strict["tools"]), 1)
        self.assertEqual(
            {k: v for k, v in strict.items() if k != "tools"},
            {k: v for k, v in plain.items() if k != "tools"},
        )
        self.assertEqual(strict["tool_choice"], {"type": "tool", "name": STRUCTURED_TOOL_NAME})
        self.assertEqual(strict["thinking"], {"type": "disabled"})
        plain_tool = dict(plain["tools"][0])
        strict_tool = dict(strict["tools"][0])
        del strict_tool[STRICT_TOOL_FLAG]
        self.assertEqual(strict_tool, plain_tool)

    def test_the_plain_adapter_still_sends_no_strict_flag(self) -> None:
        body = AnthropicProvider(api_key="k", transport=FakeTransport()).build_body(
            request(contract()), "m"
        )
        self.assertEqual(list(body["tools"][0]), ["name", "description", "input_schema"])

    def test_a_schema_with_an_unsupported_keyword_is_refused_before_a_body_exists(self) -> None:
        with self.assertRaisesRegex(ProviderInvalidRequestError, "maxLength"):
            strict_provider().build_body(request(contract()), "claude-sonnet-5")

    def test_a_request_without_a_schema_is_refused(self) -> None:
        with self.assertRaises(ProviderInvalidRequestError):
            strict_provider().build_body(request(None), "claude-sonnet-5")

    def test_no_beta_header_is_added(self) -> None:
        self.assertEqual(strict_provider()._headers(), AnthropicProvider(api_key="k")._headers())

    def test_the_completion_reading_is_the_plain_adapters(self) -> None:
        self.assertIs(AnthropicStrictToolProvider._normalize, AnthropicProvider._normalize)
        self.assertNotIn("classify_forced_tool_completion", vars(anthropic_strict))
        self.assertEqual(classify_forced_tool_completion("tool_use").value, "COMPLETE")


class TheModuleIsPure(unittest.TestCase):
    def test_it_reads_no_file_and_imports_nothing_that_could(self) -> None:
        tree = ast.parse(inspect.getsource(anthropic_strict))
        imported = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                imported.update(alias.name for alias in node.names)
            elif isinstance(node, ast.ImportFrom) and node.level == 0:
                imported.add(str(node.module))
        self.assertLessEqual(
            imported,
            {"__future__", "hashlib", "json", "collections.abc", "dataclasses", "typing"},
        )
        names = {n.id for n in ast.walk(tree) if isinstance(n, ast.Name)}
        self.assertTrue(names.isdisjoint({"open", "Path", "pathlib", "os"}))

    def test_no_literal_names_a_property_of_any_output(self) -> None:
        source = inspect.getsource(anthropic_strict)
        self.assertNotIn("parameter name", source)


if __name__ == "__main__":
    unittest.main()
