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


def local_profile(catalog_json: dict) -> dict:
    return next(p for p in catalog_json["use_profiles"] if p["use_profile_id"] == LOCAL_PROFILE)


# ============================================ gate one: the governance question


class TestTransmissionToAThirdPartyWasNeverAssessed:
    def test_the_review_permits_inference_as_an_activity(self, catalog_json) -> None:
        """Half the question is answered, and it is the half that does not
        decide anything here."""
        review = local_review(catalog_json, "stack-exchange")
        assert review["model_processing"] == "PERMITTED_WITH_CONDITIONS"
        assert "MODEL INFERENCE IS PERMITTED" in review["review_notes"]

    def test_and_the_basis_is_about_reading_not_about_transmitting(self, catalog_json) -> None:
        """The recorded basis is the licence's grant to reproduce and to produce
        Adapted Material — which answers *may a model read this*, not *may this
        leave the deployment so a third party's model can read it*."""
        notes = local_review(catalog_json, "stack-exchange")["review_notes"]
        assert "Reading and classifying licensed text" in notes
        assert "grant to reproduce and to produce Adapted Material" in notes

    def test_no_condition_on_the_review_mentions_a_provider(self, catalog_json) -> None:
        review = local_review(catalog_json, "stack-exchange")
        blob = json.dumps(review["conditions"] + review["required_conditions"]).lower()
        for word in ("provider", "third party", "third-party", "transmit", "external service"):
            assert word not in blob, word

    def test_the_profile_has_no_field_for_where_inference_happens(self, catalog_json) -> None:
        """The structural finding, pinned. `model_inference` says the ACTIVITY is
        in scope; `deployment: LOCAL` says where the SYSTEM runs. Neither says
        where inference runs, and the profile has no word for it.

        The same shape as Mission 1.15.4: a distinction the system needs, with no
        slot to record it, found by the first mission that needed it.
        """
        profile = local_profile(catalog_json)
        assert profile["model_inference"] is True
        assert profile["deployment"] == "LOCAL"
        blob = json.dumps(profile).lower()
        for word in ("provider", "third party", "third-party", "transmit", "egress"):
            assert word not in blob, word

    def test_no_repository_document_authorises_the_transfer(self) -> None:
        """Searched rather than assumed. If a later mission adds such a document,
        this test is where the absence stops being true."""
        hits = []
        for path in (REPO_ROOT / "docs").rglob("*.md"):
            text = path.read_text(encoding="utf-8", errors="ignore").lower()
            if "semantic-problem-equivalence" in path.name:
                continue  # the architecture document DESCRIBES the gap
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
        module was added that would need it."""
        interpreters = {p.stem for p in (NLP / "interpreters").glob("*.py")}
        assert interpreters == {"__init__", "base", "observed_restatement"}

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
    assert "None of the four is a code change" in architecture
