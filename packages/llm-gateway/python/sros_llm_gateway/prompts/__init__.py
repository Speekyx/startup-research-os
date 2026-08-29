"""Versioned prompts and the injection boundary (ADR-006, Mission 0.4 §28-§29).

    rendering.py   the three regions, and the type that keeps them apart
    registry.py    versioned templates, looked up by (id, version)

Nothing here imports a provider or the gateway: a prompt is an artifact, and
rendering one must not depend on who will eventually receive it.
"""

from .registry import RUNTIME_PROMPTS, PromptNotFoundError, PromptRegistry, PromptTemplate
from .rendering import (
    BOUNDARY_INSTRUCTION,
    CLOSE_DELIMITER,
    OPEN_DELIMITER,
    PromptInjectionError,
    RenderedPrompt,
    UntrustedText,
)

__all__ = [
    "PromptTemplate",
    "PromptRegistry",
    "PromptNotFoundError",
    "RUNTIME_PROMPTS",
    "RenderedPrompt",
    "UntrustedText",
    "PromptInjectionError",
    "OPEN_DELIMITER",
    "CLOSE_DELIMITER",
    "BOUNDARY_INSTRUCTION",
]
