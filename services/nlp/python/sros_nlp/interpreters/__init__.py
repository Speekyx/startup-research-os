"""Deterministic claim interpreters, and the registry of what exists.

`claim-interpretation-runtime-v1.md`. Mission 1.13.1.

**One interpreter exists** and it produces `OBSERVED` claims only. `INFERRED`,
`PREDICTED` and `RECOMMENDED` interpretation is not implemented and is not
partially implemented: there is no module for it, no branch to reach and no
parameter that would select one.

Registered here rather than discovered by import scanning, for the reason
`EXTRACTOR_REGISTRY` gives one layer down: a registry that grows by putting a
file in a directory grows by accident.
"""

from __future__ import annotations

from .base import (
    ClaimTemplate,
    InterpretationRefusedError,
    InterpretationRequest,
    SignalLineage,
    SignalView,
    TemplateOutcome,
    lineage_fact,
)
from .observed_restatement import (
    INTERPRETER_ID,
    INTERPRETER_VERSION,
    OBSERVED_EVIDENCE_LEVEL,
    SUPPORTED_SIGNAL_TYPES,
    ObservedSignalRestatementInterpreter,
)

__all__ = [
    "INTERPRETER_ID",
    "INTERPRETER_REGISTRY",
    "INTERPRETER_VERSION",
    "OBSERVED_EVIDENCE_LEVEL",
    "SUPPORTED_SIGNAL_TYPES",
    "ClaimTemplate",
    "InterpretationRefusedError",
    "InterpretationRequest",
    "ObservedSignalRestatementInterpreter",
    "SignalLineage",
    "SignalView",
    "TemplateOutcome",
    "lineage_fact",
    "select_interpreter",
]

INTERPRETER_REGISTRY: dict[str, ObservedSignalRestatementInterpreter] = {
    INTERPRETER_ID: ObservedSignalRestatementInterpreter(),
}


def select_interpreter(interpreter_id: str) -> ObservedSignalRestatementInterpreter | None:
    """The named interpreter, or nothing. There is no default.

    A job that could pick an interpreter could pick the wrong one, and an
    interpreter is the thing that decides what a proposition says.
    """
    return INTERPRETER_REGISTRY.get(interpreter_id)
