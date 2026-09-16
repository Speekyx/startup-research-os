"""Mission 1.85.1. The first-person source qualification record agrees with its own rules.

The record answers one question per frozen candidate: can local-private-research-v1 approve an official
route exposing deterministic structured evidence? These checks keep the answer honest rather than
re-deciding it: the candidate set is the one frozen before retrieval, silence never becomes an
approval, every decisive reason rests on a document re-read from its bytes, eligibility follows the
stated rule, and the roadmap says what the record says. Nothing here fetches anything.
"""

from __future__ import annotations

import hashlib
import json
import pathlib
import re
from urllib.parse import urlparse

import pytest

REPO_ROOT = pathlib.Path(__file__).resolve().parents[4]
DOCS = REPO_ROOT / "docs" / "data"
CANDIDATES = json.loads((DOCS / "first-person-source-candidates-v1.json").read_text("utf-8"))
RECORD = json.loads((DOCS / "first-person-source-qualification-v1.json").read_text("utf-8"))
ROADMAP = json.loads((DOCS / "business-evidence-acquisition-roadmap-v1.json").read_text("utf-8"))
CATALOG = json.loads((DOCS / "source-catalog-v1.json").read_text("utf-8"))
CATALOG_IDS = {s["source_id"] for s in CATALOG["sources"]}

VERDICTS = {"PERMITTED", "PERMITTED_WITH_CONDITIONS", "NOT_PERMITTED", "NOT_ADDRESSED", "UNCLEAR"}
APPROVING = set(RECORD["approving_verdicts"])
OFFICIAL_TYPES = {
    "OFFICIAL_API_DOCS",
    "OFFICIAL_TERMS",
    "OFFICIAL_LICENCE",
    "OFFICIAL_PRIVACY",
    "OFFICIAL_ACCESS_CONTROL",
}
FIRST_PARTY_HOSTS = {
    "github": ("docs.github.com", "raw.githubusercontent.com"),
    "steam": ("steampowered.com", "steamcommunity.com", "steamgames.com"),
    "google-play": ("developers.google.com", "play.google.com"),
    "apple-app-store": ("apple.com",),
    "gitlab-com": ("gitlab.com",),
    "codeberg": ("codeberg.org",),
    "kernel-org-bugzilla": ("kernel.org",),
    "trustpilot": ("trustpilot.com",),
}
#: Paths that would return research data rather than documentation.
DATA_ENDPOINT = re.compile(
    r"/appreviews/|/reviews\b|/issues\b|/rest/bug|/business-units/|/customerReviews"
)
BY_ID = {c["candidate_id"]: c for c in RECORD["candidates"]}


def _frozen_digest() -> str:
    body = {
        k: v
        for k, v in CANDIDATES.items()
        if k not in {"$comment", "frozen_set_sha256", "corrections"}
    }
    canonical = json.dumps(body, sort_keys=True, ensure_ascii=False, separators=(",", ":"))
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


class TestFrozenSet:
    def test_the_digest_recomputes(self) -> None:
        assert _frozen_digest() == CANDIDATES["frozen_set_sha256"]
        assert (
            RECORD["frozen_candidate_set"]["frozen_set_sha256"] == CANDIDATES["frozen_set_sha256"]
        )

    def test_every_frozen_candidate_is_evaluated_exactly_once(self) -> None:
        frozen = [c["candidate_id"] for c in CANDIDATES["candidates"]]
        evaluated = [c["candidate_id"] for c in RECORD["candidates"]]
        assert sorted(frozen) == sorted(evaluated)
        assert len(set(evaluated)) == len(evaluated)
        assert CANDIDATES["corrections"] == RECORD["frozen_candidate_set"]["corrections"] == []

    def test_registration_state_matches_the_catalog(self) -> None:
        unregistered = [c for c in CANDIDATES["candidates"] if not c["registered"]]
        assert len(unregistered) <= CANDIDATES["max_unregistered"] == 4
        for c in CANDIDATES["candidates"]:
            assert (c["candidate_id"] in CATALOG_IDS) is c["registered"], c["candidate_id"]


class TestEvidence:
    @pytest.mark.parametrize("candidate_id", sorted(BY_ID))
    def test_evidence_is_first_party_and_official(self, candidate_id: str) -> None:
        for row in BY_ID[candidate_id]["evidence"]:
            host = urlparse(row["url"]).hostname or ""
            assert row["url"].startswith("https://"), row["id"]
            assert any(
                host == h or host.endswith("." + h) for h in FIRST_PARTY_HOSTS[candidate_id]
            ), row["id"]
            assert row["evidence_type"] in OFFICIAL_TYPES, row["id"]
            assert row["stance"] in {"GRANTS", "RESTRICTS", "PROHIBITS", "NOT_ADDRESSED"}, row["id"]
            assert row["id"].startswith(candidate_id + "-E")

    def test_raw_verified_rows_match_a_complete_raw_read(self) -> None:
        reads = {r["url"]: r for r in RECORD["raw_reads"]}
        for candidate in RECORD["candidates"]:
            for row in candidate["evidence"]:
                if row["verification"] == "RAW_VERIFIED":
                    read = reads[row["url"]]
                    assert row["sha256"] == read["sha256"]
                    assert read["http_status"] == 200
                    assert read["phrases_verified"] and all(read["phrases_verified"].values())
                else:
                    assert row["verification"] == "SUMMARISED_FETCH" and row["sha256"] is None

    def test_no_research_data_was_retrieved_and_no_model_called(self) -> None:
        assert RECORD["no_research_data_retrieved"] is True
        assert RECORD["model_calls"] == 0
        for read in RECORD["raw_reads"]:
            assert not DATA_ENDPOINT.search(urlparse(read["url"]).path), read["url"]


class TestActivities:
    @pytest.mark.parametrize("candidate_id", sorted(BY_ID))
    def test_six_activities_are_assessed_separately(self, candidate_id: str) -> None:
        candidate = BY_ID[candidate_id]
        assert set(candidate["activities"]) == set(RECORD["required_activities"])
        assert set(candidate["activity_evidence"]) == set(RECORD["required_activities"])
        assert set(candidate["activities"].values()) <= VERDICTS

    @pytest.mark.parametrize("candidate_id", sorted(BY_ID))
    def test_a_verdict_other_than_silence_cites_evidence(self, candidate_id: str) -> None:
        candidate = BY_ID[candidate_id]
        ids = {row["id"] for row in candidate["evidence"]}
        for activity, verdict in candidate["activities"].items():
            cited = candidate["activity_evidence"][activity]
            assert set(cited) <= ids, (candidate_id, activity)
            if verdict != "NOT_ADDRESSED":
                assert cited, (candidate_id, activity)

    @pytest.mark.parametrize("candidate_id", sorted(BY_ID))
    def test_silence_is_never_an_approval(self, candidate_id: str) -> None:
        candidate = BY_ID[candidate_id]
        rows = {row["id"]: row for row in candidate["evidence"]}
        for activity, verdict in candidate["activities"].items():
            if verdict in APPROVING:
                stances = {rows[i]["stance"] for i in candidate["activity_evidence"][activity]}
                assert "GRANTS" in stances, (candidate_id, activity)


class TestEligibility:
    @pytest.mark.parametrize("candidate_id", sorted(BY_ID))
    def test_eligibility_follows_the_rule(self, candidate_id: str) -> None:
        candidate = BY_ID[candidate_id]
        gate = candidate["eligibility"]
        approving = all(v in APPROVING for v in candidate["activities"].values())
        assert gate["all_activities_approving"] is approving
        expected = (
            approving
            and gate["structured_field"] in {"PASS", "PARTIAL"}
            and gate["conflicting_binding_restriction"] is False
            and gate["provenance_sufficient"] is True
        )
        assert gate["eligible"] is expected

    @pytest.mark.parametrize("candidate_id", sorted(BY_ID))
    def test_a_decisive_reason_rests_on_a_document_read_from_its_bytes(
        self, candidate_id: str
    ) -> None:
        candidate = BY_ID[candidate_id]
        rows = {row["id"]: row for row in candidate["evidence"]}
        assert candidate["decisive_reasons"]
        for reason in candidate["decisive_reasons"]:
            assert any(rows[i]["verification"] == "RAW_VERIFIED" for i in reason["evidence"]), (
                reason
            )

    def test_the_outcome_follows_from_the_candidates(self) -> None:
        eligible = sorted(
            c["candidate_id"] for c in RECORD["candidates"] if c["eligibility"]["eligible"]
        )
        assert RECORD["eligible_candidates"] == eligible
        if eligible:
            assert RECORD["outcome"] == "SUCCESS"
            assert RECORD["selected_source"] in eligible and RECORD["selected_resource"]
        else:
            assert RECORD["outcome"] == "NO_GO"
            assert RECORD["selected_source"] is None and RECORD["selected_resource"] is None
            assert {"A", "B"} <= set(RECORD["operator_decision_required"])

    def test_nothing_was_registered_or_reviewed_without_an_approving_basis(self) -> None:
        if RECORD["outcome"] == "NO_GO":
            assert RECORD["source_reviews_appended"] == []
            assert RECORD["sources_registered"] == []
        for candidate in RECORD["candidates"]:
            registered = candidate["registration"] == "REGISTERED"
            assert registered is (candidate["candidate_id"] in CATALOG_IDS)


class TestRoadmapAgreement:
    def test_n01_and_n02_reflect_the_outcome(self) -> None:
        nodes = {n["id"]: n for n in ROADMAP["nodes"]}
        result = ROADMAP["mission_1_85_1_result"]
        assert result["outcome"] == RECORD["outcome"]
        assert result["eligible"] == len(RECORD["eligible_candidates"])
        assert result["candidates_evaluated"] == len(RECORD["candidates"])
        if RECORD["outcome"] == "NO_GO":
            assert nodes["N01"]["status"] == "NO_GO_OPERATOR_DECISION_REQUIRED"
            assert nodes["N02"]["bound_family"] is None
        else:
            assert nodes["N01"]["status"] == "DONE"
            assert nodes["N02"]["bound_family"] is not None
