"""Why no model was called, and what would have to change.

Mission 1.22, **Outcome A**. This encodes a DECISION rather than a behaviour, the
shape Missions 1.20 and 1.21 use — and here it also guards a boundary, because
the thing not built is the first component in this repository that would assert
something the source never said.

**Two gates refused, independently.** Governance: no review, profile field or
policy document authorises transmitting licensed source content to an external
provider. Configuration: every inference tier is `null`, every credential is
empty, and no local inference provider exists.

Neither gate can be opened by the other, and neither is opened by a code change.
"""

from __future__ import annotations

import json

import pytest

from .conftest import LOCAL_PROFILE, REPO_ROOT

CATALOG = REPO_ROOT / "docs" / "data" / "source-catalog-v1.json"
ARCHITECTURE = REPO_ROOT / "docs" / "data" / "semantic-problem-equivalence-v1.md"
ENV = REPO_ROOT / "infrastructure" / "compose" / ".env.example"
GATEWAY = REPO_ROOT / "packages" / "llm-gateway" / "python" / "sros_llm_gateway"
NLP = REPO_ROOT / "services" / "nlp" / "python" / "sros_nlp"


@pytest.fixture(scope="module")
def catalog_json() -> dict:
    return json.loads(CATALOG.read_text(encoding="utf-8"))


def local_review(catalog_json: dict, source_id: str) -> dict:
    entry = next(s for s in catalog_json["sources"] if s["source_id"] == source_id)
    reviews = [r for r in entry["reviews"] if r["assessed_use_profile"] == LOCAL_PROFILE]
    return max(reviews, key=lambda r: r["review_version"])


def review_version(catalog_json: dict, source_id: str, version: int) -> dict:
    """One SPECIFIC version, for assertions about what a review said at a point
    in time.

    `local_review` returns the newest, which is what runtime cares about. The
    tests below that describe what Mission 1.22 FOUND must pin the version they
    found it in: reviews are append-only, so v1 remains readable forever, and an
    assertion about it that silently followed the latest version would stop
    describing history the moment a later mission appended.
    """
    entry = next(s for s in catalog_json["sources"] if s["source_id"] == source_id)
    return next(
        r
        for r in entry["reviews"]
        if r["assessed_use_profile"] == LOCAL_PROFILE and r["review_version"] == version
    )


def local_profile(catalog_json: dict) -> dict:
    return next(p for p in catalog_json["use_profiles"] if p["use_profile_id"] == LOCAL_PROFILE)


# ============================================ gate one: the governance question


class TestTransmissionToAThirdPartyWasNeverAssessed:
    def test_the_review_permits_inference_as_an_activity(self, catalog_json) -> None:
        """Half the question is answered, and it is the half that does not
        decide anything here."""
        review = review_version(catalog_json, "stack-exchange", 1)
        assert review["model_processing"] == "PERMITTED_WITH_CONDITIONS"
        assert "MODEL INFERENCE IS PERMITTED" in review["review_notes"]
        # and it is still the answer, carried forward unchanged into v2
        assert local_review(catalog_json, "stack-exchange")["model_processing"] == (
            "PERMITTED_WITH_CONDITIONS"
        )

    def test_and_the_basis_is_about_reading_not_about_transmitting(self, catalog_json) -> None:
        """The recorded basis is the licence's grant to reproduce and to produce
        Adapted Material — which answers *may a model read this*, not *may this
        leave the deployment so a third party's model can read it*."""
        notes = review_version(catalog_json, "stack-exchange", 1)["review_notes"]
        assert "Reading and classifying licensed text" in notes
        assert "grant to reproduce and to produce Adapted Material" in notes

    def test_v1_asked_nothing_about_a_provider_and_v2_asks_for_a_property(
        self, catalog_json
    ) -> None:
        """Mission 1.22 found that no condition mentioned a provider, as evidence
        that the question had never been asked. Mission 1.23 asked it, and this
        assertion moved rather than being deleted.

        **v2 still names no vendor.** Its condition expresses the PROPERTY a
        provider must have -- no training on submitted content, documented
        bounded retention -- because a source review that named a company would
        need re-versioning every time a provider list changed, and would put
        provider governance inside the source registry where it does not belong.
        """
        v1 = review_version(catalog_json, "stack-exchange", 1)
        was = json.dumps(v1["conditions"] + v1["required_conditions"]).lower()
        for word in ("provider", "third party", "third-party", "transmit", "external service"):
            assert word not in was, word

        v2 = review_version(catalog_json, "stack-exchange", 2)
        now = json.dumps(v2["conditions"] + v2["required_conditions"]).lower()
        assert "external model provider" in now
        for vendor in ("anthropic", "gemini", "openai", "google", "mistral"):
            assert vendor not in now, vendor
        assert v2["external_model_transmission"] == "PERMITTED_WITH_CONDITIONS"
        assert "external_model_transmission" not in v1, "v1 must not be rewritten"

    def test_the_profile_now_has_the_field_it_was_missing(self, catalog_json) -> None:
        """The structural finding, and its repair.

        Mission 1.22 found that `model_inference` said the ACTIVITY was in scope
        and `deployment: LOCAL` said where the SYSTEM ran, while nothing said
        where inference RUNS -- the same shape as Mission 1.15.4, a distinction
        the system needed with no slot to record it. ADR-033 added
        `external_model_egress`, and this assertion moved from *the field is
        absent* to *the field exists and every profile states it in its own
        words*.

        The two older fields are asserted UNCHANGED. The repair was to add a
        word, not to reinterpret `deployment` as a claim about processing
        location, which would have granted a permission nobody assessed.
        """
        profile = local_profile(catalog_json)
        assert profile["model_inference"] is True
        assert profile["deployment"] == "LOCAL"
        assert profile["external_model_egress"] == "PERMITTED_TO_APPROVED_PROVIDERS"

        # The commercial profile refuses, and refuses as an OPEN QUESTION rather
        # than as a decision -- stated explicitly, not inherited from a default.
        commercial = next(
            p
            for p in catalog_json["use_profiles"]
            if p["use_profile_id"] == "commercial-multi-tenant-research-v1"
        )
        assert commercial["external_model_egress"] == "NOT_ASSESSED"

    def test_the_activity_the_contract_could_not_express_now_exists(self) -> None:
        """The precise defect Mission 1.22 named: one field answering a question
        that is two."""
        from sros_acquisition.registry.models import ASSESSED_ACTIVITIES

        assert "model_processing" in ASSESSED_ACTIVITIES
        assert "external_model_transmission" in ASSESSED_ACTIVITIES

    def test_the_authorising_document_now_exists_and_still_refuses(self) -> None:
        """Mission 1.22 searched every document rather than assuming, and found
        none that authorised the transfer. Its docstring said this test was
        where that absence would stop being true. Mission 1.23 is that mission.

        So the assertion inverts: the document exists, and what it authorises is
        CONDITIONAL. It must still state that nothing has been sent -- an
        authorising document that quietly dropped the open gate would be the
        failure mode this test was written to catch.
        """
        doc = REPO_ROOT / "docs" / "data" / "model-inference-execution-governance-v1.md"
        assert doc.exists()
        text = doc.read_text(encoding="utf-8")
        assert "PROVIDER_NOT_CONFIGURED" in text
        assert "authorises no transmission" in text
        assert "commercial-multi-tenant-research-v1" in text and "NOT_ASSESSED" in text

    def test_no_other_document_authorises_it_by_a_side_door(self) -> None:
        """The original search, kept. One document may authorise this, under
        gates; a second one appearing elsewhere would mean the boundary had been
        restated somewhere it is not governed.
        """
        allowed = {
            "semantic-problem-equivalence-v1.md",  # DESCRIBES the gap
            "model-inference-execution-governance-v1.md",  # governs it
            "mission-1.23-report.md",  # reports this mission
        }
        hits = []
        for path in (REPO_ROOT / "docs").rglob("*.md"):
            if path.name in allowed:
                continue
            text = path.read_text(encoding="utf-8", errors="ignore").lower()
            if "authorised to send" in text or "may transmit source content" in text:
                hits.append(path.name)
        assert not hits, hits


# ======================================== gate two: no route exists to prefer


class TestNoInferenceRouteIsConfigured:
    def test_every_inference_tier_is_unconfigured(self) -> None:
        """`null` is what `config.py` treats as *not configured*: the tier
        predicate is `bool(self.provider) and self.provider != "null"`."""
        template = ENV.read_text(encoding="utf-8")
        for tier in ("FAST", "BALANCED", "STRONG"):
            assert f"LLM_TIER_{tier}_PROVIDER=null" in template, tier

    def test_the_only_non_null_tier_is_the_forbidden_one(self) -> None:
        """`local` appears once, as the EMBEDDING tier — and embeddings are
        forbidden by D-12 and by this mission's §7. So §6's instruction to prefer
        a local inference provider has no candidate to prefer."""
        template = ENV.read_text(encoding="utf-8")
        assert "LLM_TIER_EMBEDDING_PROVIDER=local" in template

    def test_no_local_inference_provider_exists_in_the_repository(self) -> None:
        modules = {p.stem for p in (GATEWAY / "providers").glob("*.py")}
        assert modules == {"__init__", "anthropic", "gemini", "fake"}
        # Both real providers are external services; `fake` is a test double.
        assert "local" not in modules
        assert "ollama" not in modules

    def test_the_two_gates_are_independent(self) -> None:
        """Stated as an assertion because it decides what a later mission must
        do: configuring a provider would not answer the governance question, and
        answering it would not configure a provider."""
        architecture = ARCHITECTURE.read_text(encoding="utf-8")
        assert "The two gates are independent" in architecture


# =================================================== nothing was built or run


class TestNothingWasBuiltAndNothingWasCalled:
    def test_no_semantic_equivalence_component_exists(self) -> None:
        for name in ("equivalence", "inference", "similarity", "rubric", "classifier"):
            assert not list(NLP.rglob(f"*{name}*.py")), name

    def test_no_inferred_claim_interpreter_exists(self) -> None:
        """`validate_claims.py` already fails the build on a non-OBSERVED claim
        type in the interpretation package. This asserts the simpler fact: no
        module was added that would need it.

        The enumeration is deliberate -- a new module has to be argued for here
        rather than appearing. `convergent_witness` was added by Mission 1.39 and
        is structurally OBSERVED: it projects one OBSERVED draft onto a broader
        OBSERVED proposition, and `PropositionConvergenceContract` refuses a
        non-OBSERVED claim type in its constructor.

        The property is asserted below rather than left to the names, because a
        module list is only evidence about what exists and not about what it
        does.
        """
        interpreters = {p.stem for p in (NLP / "interpreters").glob("*.py")}
        assert interpreters == {
            "__init__",
            "base",
            "observed_restatement",
            "convergent_witness",
        }

    def test_every_interpreter_module_is_structurally_observed(self) -> None:
        """The property the enumeration above is a proxy for.

        Parsed over the AST so a docstring naming `ClaimType.INFERRED` -- as the
        surrounding prose reasonably might -- cannot fail it
        (`testing-strategy.md` §23).
        """
        import ast

        for path in (NLP / "interpreters").glob("*.py"):
            tree = ast.parse(path.read_text(encoding="utf-8"))
            for node in ast.walk(tree):
                if (
                    isinstance(node, ast.Attribute)
                    and isinstance(node.value, ast.Name)
                    and node.value.id == "ClaimType"
                ):
                    assert node.attr == "OBSERVED", f"{path.name} names ClaimType.{node.attr}"

    def test_no_prompt_was_added_for_semantic_equivalence(self) -> None:
        prompts = GATEWAY / "prompts"
        if prompts.exists():
            for path in prompts.rglob("*"):
                if path.is_file():
                    text = path.read_text(encoding="utf-8", errors="ignore").lower()
                    assert "same_problem" not in text
                    assert "problem-equivalence" not in text

    def test_the_corpus_was_not_re_acquired(self) -> None:
        """§3 and §41. The existing 104 `community_question` observations are the
        corpus; no query was run and none could have been, since the mission
        stopped before any inference work."""
        architecture = ARCHITECTURE.read_text(encoding="utf-8")
        assert "No inference was performed and no model was called" in architecture


# ================================================ the deterministic results hold


class TestTheDeterministicFindingsAreNotContradicted:
    def test_unavailable_deterministically_is_not_impossible_semantically(self) -> None:
        """§38, and it is the distinction that keeps Missions 1.18 and 1.20 true.

        They established that DETERMINISTIC identity is unavailable over this
        corpus. That is a statement about a method. A later model inferring
        equivalence would contradict neither, and the architecture document says
        so in those words so a reader cannot collapse them.
        """
        architecture = ARCHITECTURE.read_text(encoding="utf-8")
        assert "Deterministic identity unavailable" in architecture
        assert "not" in architecture and "semantic equivalence impossible" in architecture

    def test_the_docker_hard_negatives_are_carried_into_the_design(self) -> None:
        """§26. The three questions sharing the 182-character wrapper are named
        in the rubric section as the cases a rubric must not collapse — recorded
        now so they are not rediscovered later."""
        architecture = ARCHITECTURE.read_text(encoding="utf-8")
        assert "182 characters" in architecture or "182-character" in architecture
        assert "permission denied" in architecture
        assert "executable file not found in $PATH" in architecture


def test_the_design_records_what_would_have_to_change() -> None:
    """A blocked mission that recorded only *blocked* would make the next one
    start over. Four preconditions are named, and none of them is a code
    change."""
    architecture = ARCHITECTURE.read_text(encoding="utf-8")
    assert "What would have to be true before this is built" in architecture
    # Mission 1.23 §0 corrected the closing sentence: the original claimed none of
    # the four was a code change, which is untrue of the profile field and of a
    # local provider. What must hold is that none may be silently inferred.
    assert "may be silently inferred from the current configuration" in architecture
    assert "contract and schema change" in architecture
