"""The orchestrator's readiness check and the acquisition gate must agree.

Mission 1.24 §0.A. `sros_orchestrator.inference_readiness` reads governance from
the DATABASE and `sros_acquisition.compliance.inference` computes the same
verdicts from the CATALOG in Python, for review tooling. Neither package imports
the other, which is correct and is exactly what lets them drift.

`sources.py` set this precedent for eligibility -- *"`sros_acquisition` computes
the same verdict in Python for review tooling, and a test asserts the two agree
rather than assuming it"* -- and this module is that test for the ADR-033 gates.

**The cross-package import lives in a TEST**, which is the only place it belongs:
a test may know about two packages in order to compare them, while neither may
know about the other in order to work.
"""

from __future__ import annotations

import json

import pytest
from sros_acquisition.compliance.inference import APPROVING_ASSESSMENTS
from sros_acquisition.registry.models import (
    EGRESS_PERMITTED_TO_APPROVED_PROVIDERS,
    EXTERNAL_MODEL_EGRESS_STATES,
)
from sros_orchestrator import inference_readiness as readiness

from .conftest import LOCAL_PROFILE, REPO_ROOT

CATALOG = REPO_ROOT / "docs" / "data" / "source-catalog-v1.json"


@pytest.fixture(scope="module")
def review() -> dict:
    raw = json.loads(CATALOG.read_text(encoding="utf-8"))
    entry = next(s for s in raw["sources"] if s["source_id"] == "stack-exchange")
    local = [r for r in entry["reviews"] if r["assessed_use_profile"] == LOCAL_PROFILE]
    return max(local, key=lambda r: r["review_version"])


@pytest.fixture(scope="module")
def profile() -> dict:
    raw = json.loads(CATALOG.read_text(encoding="utf-8"))
    return next(p for p in raw["use_profiles"] if p["use_profile_id"] == LOCAL_PROFILE)


class TestTheTwoImplementationsAgreeOnTheVocabulary:
    def test_the_approving_assessments_are_the_same_set(self) -> None:
        """The readiness module keeps a string mirror of a `PolicyAssessment`
        set, because it must not import the acquisition package. A mirror is a
        copy, and a copy that nothing compares is a copy that drifts."""
        assert {a.value for a in APPROVING_ASSESSMENTS} == readiness._APPROVING

    def test_the_permitting_egress_state_is_the_same_string(self) -> None:
        assert readiness._EGRESS_PERMITTED == EGRESS_PERMITTED_TO_APPROVED_PROVIDERS

    def test_the_permitting_state_is_one_the_contract_recognises(self) -> None:
        """A typo here would read as a state nobody defined, and a state nobody
        defined never equals the stored value, so the gate would refuse forever
        while looking like it was working."""
        assert readiness._EGRESS_PERMITTED in EXTERNAL_MODEL_EGRESS_STATES

    def test_exactly_one_egress_state_permits(self) -> None:
        """Three states, one of which permits. If a later mission adds a second
        permitting state, this fails and the readiness mirror has to be updated
        deliberately rather than discovered in production."""
        permitting = {s for s in EXTERNAL_MODEL_EGRESS_STATES if "PERMITTED" in s}
        assert permitting == {EGRESS_PERMITTED_TO_APPROVED_PROVIDERS}


class TestTheReadinessGatesMatchTheCatalogThisDeploymentRuns:
    """Read from the committed catalog rather than the database, so this runs
    with no PostgreSQL. The database is what the readiness check actually reads;
    what is asserted here is that the two sources of truth say the same thing."""

    def test_the_governance_gates_would_pass_on_the_committed_catalog(
        self, review: dict, profile: dict
    ) -> None:
        """All three governance gates, evaluated against the catalog with the
        readiness module's own vocabulary."""
        assert review["model_processing"] in readiness._APPROVING
        assert review["external_model_transmission"] in readiness._APPROVING
        assert profile["external_model_egress"] == readiness._EGRESS_PERMITTED

    def test_the_commercial_profile_would_not_pass(self) -> None:
        """The same check under the other profile refuses, and refuses because
        the question is open rather than because it was decided against."""
        raw = json.loads(CATALOG.read_text(encoding="utf-8"))
        commercial = next(
            p
            for p in raw["use_profiles"]
            if p["use_profile_id"] == "commercial-multi-tenant-research-v1"
        )
        assert commercial["external_model_egress"] != readiness._EGRESS_PERMITTED
        assert commercial["external_model_egress"] == "NOT_ASSESSED"


class TestTheReadinessCheckIsNotAnAuthorization:
    def test_it_produces_no_authorization_object(self) -> None:
        """Readiness says a call would be routable and permitted. The decision a
        caller must hold before serialising source text is still
        `authorize_external_inference`, and nothing in the orchestrator
        substitutes for it."""
        assert not hasattr(readiness, "authorize_external_inference")
        exported = set(readiness.__all__)
        assert not any("authoriz" in name.lower() for name in exported)

    def test_the_readiness_module_imports_no_provider_sdk(self) -> None:
        """It reports configuration; it never reaches one."""
        import ast
        import pathlib

        path = pathlib.Path(readiness.__file__)
        tree = ast.parse(path.read_text(encoding="utf-8"))
        roots = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                roots |= {a.name.split(".")[0] for a in node.names}
            elif isinstance(node, ast.ImportFrom) and node.module and node.level == 0:
                roots.add(node.module.split(".")[0])
        for forbidden in ("anthropic", "httpx", "requests", "openai", "google"):
            assert forbidden not in roots, forbidden
