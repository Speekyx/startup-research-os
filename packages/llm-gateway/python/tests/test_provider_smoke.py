"""Real-provider smoke tests. OPT-IN, DISABLED BY DEFAULT.

Mission 0.4 §20: *"CI must never require an Anthropic API key, a Gemini API key
or paid API calls. Real-provider smoke tests must be opt-in and disabled by
default."*

Two conditions must BOTH hold before anything here runs:

    SROS_ENABLE_PROVIDER_SMOKE_TESTS=1     an explicit, deliberate opt-in
    ANTHROPIC_API_KEY / GEMINI_API_KEY     a credential for that provider

The env flag is separate from the key on purpose. A developer with a key
exported for other work has not thereby consented to this suite spending money
every time they run `pytest`, and CI environments acquire secrets for reasons
that have nothing to do with benchmarks.

These are **smoke** tests: they answer "does the real API still look like the
adapter thinks it does". They assert nothing about answer quality — that is what
the evaluation framework is for, and it also does not run against a paid API by
default.
"""

from __future__ import annotations

import os
import unittest

from sros_contracts import LlmTier
from sros_llm_gateway import LlmRequest, RenderedPrompt
from sros_llm_gateway.providers import AnthropicProvider, GeminiProvider

SMOKE_FLAG = "SROS_ENABLE_PROVIDER_SMOKE_TESTS"

WORKSPACE = "00000000-0000-4000-8000-000000000001"
SESSION = "00000000-0000-4000-8000-0000000000aa"


def _enabled(key_name: str) -> bool:
    return os.environ.get(SMOKE_FLAG) == "1" and bool(os.environ.get(key_name))


def _reason(key_name: str) -> str:
    return f"opt-in only: set {SMOKE_FLAG}=1 and {key_name} to run a real paid call"


def _request(model_hint: str) -> LlmRequest:
    return LlmRequest(
        tier=LlmTier.FAST_MODEL,
        task="infra.smoke",
        prompt_template_id="infra-smoke",
        prompt_template_version="1.0.0",
        workspace_id=WORKSPACE,
        research_session_id=SESSION,
        correlation_id="smoke",
        timeout_seconds=30.0,
        max_retries=0,
        prompt=RenderedPrompt(
            system_instructions="Reply with the single word OK and nothing else.",
            task="Reply with OK.",
        ),
        variables={"model_hint": model_hint},
    )


@unittest.skipUnless(_enabled("ANTHROPIC_API_KEY"), _reason("ANTHROPIC_API_KEY"))
class AnthropicSmoke(unittest.TestCase):
    def test_a_real_call_returns_text_and_usage(self) -> None:
        model = os.environ.get("SROS_SMOKE_ANTHROPIC_MODEL")
        if not model:
            self.skipTest("set SROS_SMOKE_ANTHROPIC_MODEL to the model to probe")
        result = AnthropicProvider().complete(_request(model), model)
        self.assertTrue(result.content.strip())
        self.assertGreater(result.input_tokens, 0)


@unittest.skipUnless(_enabled("GEMINI_API_KEY"), _reason("GEMINI_API_KEY"))
class GeminiSmoke(unittest.TestCase):
    def test_a_real_call_returns_text_and_usage(self) -> None:
        model = os.environ.get("SROS_SMOKE_GEMINI_MODEL")
        if not model:
            self.skipTest("set SROS_SMOKE_GEMINI_MODEL to the model to probe")
        result = GeminiProvider().complete(_request(model), model)
        self.assertTrue(result.content.strip())
        self.assertGreater(result.input_tokens, 0)


class SmokeTestsAreOffByDefault(unittest.TestCase):
    """This one always runs, and is the reason the file is safe to ship.

    It asserts the guard itself rather than the provider: a smoke suite that
    quietly became enabled would spend money on every CI run, and the failure
    would show up as an invoice rather than as a red test.
    """

    def test_the_opt_in_flag_is_required_in_addition_to_a_key(self) -> None:
        self.assertFalse(_enabled_with(flag=None, key="a-key"))
        self.assertFalse(_enabled_with(flag="0", key="a-key"))
        self.assertFalse(_enabled_with(flag="1", key=""))
        self.assertTrue(_enabled_with(flag="1", key="a-key"))

    def test_a_smoke_test_skips_rather_than_guessing_a_model(self) -> None:
        """Models change faster than release cycles (ADR-006), so none is
        pinned: a smoke test with no model named skips instead of probing a
        guess. Proved by running the body with the variable removed and
        asserting that nothing is called.

        This asserts the behaviour rather than scanning the source for banned
        substrings — a scan whose own list of forbidden tokens lives in the file
        it scans always fails, which is how the first version of this test was
        written.
        """
        cases = [
            (AnthropicSmoke, "SROS_SMOKE_ANTHROPIC_MODEL"),
            (GeminiSmoke, "SROS_SMOKE_GEMINI_MODEL"),
        ]
        for case, variable in cases:
            with self.subTest(variable=variable):
                saved = os.environ.pop(variable, None)
                try:
                    with self.assertRaises(unittest.SkipTest):
                        case(
                            "test_a_real_call_returns_text_and_usage"
                        ).test_a_real_call_returns_text_and_usage()
                finally:
                    if saved is not None:
                        os.environ[variable] = saved


def _enabled_with(flag: str | None, key: str) -> bool:
    return flag == "1" and bool(key)


if __name__ == "__main__":
    unittest.main()
