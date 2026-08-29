"""Versioned prompt template registry.

Mission 0.4 §28. ADR-006 §Prompt versioning: *"Every prompt is a versioned
template artifact with an id and a version. Prompts are never assembled ad hoc
at a call site. A prompt change is a version bump, reviewed like code — because
it changes system behavior as much as code does."*

**This registry is deliberately empty of product prompts, and it is not an
oversight.** It holds the prompts the *product* sends at runtime. Every context
that would own one — `nlp` extraction, `execution` planning — is blocked or out
of scope (D-07, D-03, D-12, §34), so registering a classification prompt now
would mean writing one against a signal shape nothing produces. It would be
tested only against its own assumptions, and it would be the first thing
rewritten when the real inputs arrive.

The registry is empty; the machinery is real and tested. That is the same split
the planner makes.

It is also **not** a place for development prompts. The instructions given to a
coding agent are not runtime artifacts and do not belong in the shipped package.
"""

from __future__ import annotations

import string
from dataclasses import dataclass, field

from .rendering import PromptInjectionError, RenderedPrompt, UntrustedText

__all__ = ["PromptTemplate", "PromptRegistry", "PromptNotFoundError", "RUNTIME_PROMPTS"]


class PromptNotFoundError(LookupError):
    """No template with that id and version.

    Version is part of the lookup on purpose. Resolving "the latest" would let a
    prompt change alter the behaviour of running code without anything
    recording that it had, which is precisely what the version exists to stop.
    """


@dataclass(frozen=True)
class PromptTemplate:
    """One versioned prompt artifact.

    The schemas are declared here rather than at the call site so a caller
    cannot quietly widen what it accepts back from a model. `output_schema` is
    what the gateway validates the response against; a response that does not
    match is a schema failure, and a schema failure is treated as a possible
    injection signal rather than retried into a fallback (ADR-006).
    """

    prompt_id: str
    version: str
    purpose: str
    system_instructions: str
    task_template: str = ""
    input_schema: dict[str, object] = field(default_factory=dict)
    output_schema: dict[str, object] = field(default_factory=dict)
    change_notes: str = ""

    def __post_init__(self) -> None:
        if not self.prompt_id or not self.version:
            raise ValueError("a prompt template requires an id and a version")
        if not self.purpose.strip():
            raise ValueError(
                "a prompt template requires a stated purpose: a template nobody can "
                "explain is a template nobody can review"
            )
        if not self.system_instructions.strip():
            raise ValueError("a prompt template requires system instructions")

    @property
    def key(self) -> tuple[str, str]:
        return (self.prompt_id, self.version)

    def required_variables(self) -> frozenset[str]:
        """Placeholders the task template expects."""
        return frozenset(
            name for _, name, _, _ in string.Formatter().parse(self.task_template) if name
        )

    def render(
        self,
        variables: dict[str, object] | None = None,
        trusted_context: str = "",
        untrusted: tuple[UntrustedText, ...] = (),
    ) -> RenderedPrompt:
        """Produce a prompt with its regions separated.

        Variables are interpolated into the TASK region only, and an
        `UntrustedText` passed as a variable is refused rather than stringified:
        `str()` on it would produce a dataclass repr in the middle of an
        instruction, which is both wrong and the shape of an injection.
        """
        values = dict(variables or {})
        for name, value in values.items():
            if isinstance(value, UntrustedText):
                raise PromptInjectionError(
                    f"variable {name!r} is UntrustedText. External content belongs in the "
                    "untrusted region, never interpolated into the task."
                )

        missing = self.required_variables() - set(values)
        if missing:
            raise KeyError(
                f"prompt {self.prompt_id}@{self.version} is missing variables: {sorted(missing)}"
            )

        task = self.task_template.format(**values) if self.task_template else ""
        return RenderedPrompt(
            system_instructions=self.system_instructions,
            trusted_context=trusted_context,
            untrusted=untrusted,
            task=task,
            metadata={"prompt_id": self.prompt_id, "prompt_version": self.version},
        )


class PromptRegistry:
    """Templates keyed by (id, version). Immutable once registered."""

    def __init__(self, templates: tuple[PromptTemplate, ...] = ()) -> None:
        self._templates: dict[tuple[str, str], PromptTemplate] = {}
        for template in templates:
            self.register(template)

    def register(self, template: PromptTemplate) -> None:
        if template.key in self._templates:
            raise ValueError(
                f"prompt {template.prompt_id}@{template.version} is already registered. "
                "A prompt change is a version bump, not an overwrite: overwriting one "
                "would change the behaviour of everything that recorded the old version "
                "while leaving the record saying otherwise (ADR-006)."
            )
        self._templates[template.key] = template

    def get(self, prompt_id: str, version: str) -> PromptTemplate:
        try:
            return self._templates[(prompt_id, version)]
        except KeyError:
            available = sorted(f"{i}@{v}" for i, v in self._templates)
            raise PromptNotFoundError(
                f"no prompt {prompt_id}@{version}. Registered: {available or 'none'}"
            ) from None

    def versions(self, prompt_id: str) -> tuple[str, ...]:
        return tuple(sorted(v for i, v in self._templates if i == prompt_id))

    def __len__(self) -> int:
        return len(self._templates)

    def __contains__(self, key: object) -> bool:
        return key in self._templates


# The registry of prompts the product sends at runtime.
#
# EMPTY, deliberately. See the module docstring: every context that would own a
# runtime prompt is blocked or out of scope, and a prompt written against inputs
# nothing produces would be tested only against its own assumptions.
RUNTIME_PROMPTS: tuple[PromptTemplate, ...] = ()
