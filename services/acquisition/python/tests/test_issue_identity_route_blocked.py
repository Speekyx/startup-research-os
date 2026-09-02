"""Why the explicit-issue-identity route is blocked, source by source.

Mission 1.21. This encodes a DECISION rather than a behaviour, the same shape
`test_narrow_tool_problem_signature.py` uses for Mission 1.20 -- and for the same
reason: a mission that acquires nothing owes the tests that pin why, or it is
indistinguishable from one that gave up.

**The structure exists.** Three public trackers document a publisher-declared
canonical duplicate relation as issue state, which is what Mission 1.20 said the
next route would need. Nothing here disputes that.

**The access does not.** Every candidate that publishes a usable data licence
also publishes a robots directive disallowing the API path, and the only
deployment whose directive permits the API path publishes no data licence at all.

**Why these assertions read a DOCUMENT rather than the catalog.** Neither
candidate is registered, and that is a finding rather than an omission. A source
registered today must carry a LEGACY-profile review -- `SourceRecord.review`
allows `None`, but eighteen tests and two generated documents assume it is
present -- and these two were assessed only under `local-private-research-v1`.
Registering one would mean making the legacy review optional catalog-wide, which
is an architectural change deserving its own mission and an ADR rather than a
source mission's diff. The evidence lives in
`docs/data/issue-identity-candidates-v1.md`, which is Authoritative.
"""

from __future__ import annotations

import json

from .conftest import REPO_ROOT

CANDIDATES = REPO_ROOT / "docs" / "data" / "issue-identity-candidates-v1.md"
CATALOG = REPO_ROOT / "docs" / "data" / "source-catalog-v1.json"


def document() -> str:
    return CANDIDATES.read_text(encoding="utf-8")


# ============================================ the structure genuinely exists


class TestTheIdentityRelationIsReal:
    """Mission 1.20's proposed next route is not imaginary, and saying so
    matters: this mission's conclusion is about ACCESS, and it would be a
    different and weaker conclusion if the data model had not existed."""

    def test_the_relation_is_issue_state_and_not_a_similarity_heuristic(self) -> None:
        """§5. `dupe_of` is a field on the bug carrying another bug's id -- not a
        suggestion, a score or a search result. Quoted from the official Bugzilla
        REST documentation."""
        assert "The bug ID of the bug that this bug is a duplicate of" in document()

    def test_three_independent_shapes_pass_the_structural_gate(self) -> None:
        text = document()
        for shape in ("Bugzilla", "Launchpad", "Debian BTS"):
            assert shape in text, shape
        assert "`dupe_of`" in text
        assert "`duplicate_of_link`" in text

    def test_the_heuristic_shapes_are_excluded_by_name(self) -> None:
        """§5 refuses a possible-duplicate suggestion as the canonical relation.
        GitLab and GitHub are recorded as failing the gate rather than left
        unmentioned, so a later reader does not re-check them."""
        text = document()
        assert "GitLab" in text and "GitHub" in text
        assert "no canonical field" in text


# ==================================================== and access is refused


class TestEveryCandidateIsBlocked:
    def test_the_conclusion_is_recorded_in_the_authoritative_document(self) -> None:
        assert "BLOCKED BY SOURCE GOVERNANCE" in document()

    def test_the_blocker_is_an_access_directive_not_a_missing_licence(self) -> None:
        """The finding that makes this mission's conclusion sharp. TDF's data
        rights are favourable on every axis the profile needs; what refuses the
        source is the layer above."""
        text = document()
        assert "CC BY-SA 4.0" in text
        assert "Disallow: /" in text
        assert "/rest/" in text

    def test_the_robots_file_is_shown_to_be_curated_rather_than_boilerplate(self) -> None:
        """The detail that turns an inference into a reading: the file allows one
        CGI and disallows a query string on that same CGI, so its author was
        making choices."""
        assert "show_bug.cgi*ctype=*" in document()

    def test_launchpad_carries_two_independent_blockers(self) -> None:
        """And the second does not depend on permission: an API with no field
        selection cannot be minimised at acquisition, whatever its terms say."""
        text = document()
        assert "41 fields" in text
        assert "owner_link" in text
        assert "Blocker 1, access" in text
        assert "Blocker 2, minimisation" in text

    def test_the_one_permissive_directive_belongs_to_an_unlicensed_deployment(self) -> None:
        """`bugzilla.kernel.org` is the only deployment whose robots directive
        allows the API path, and it licenses nothing. That symmetry is the
        result."""
        text = document()
        assert "kernel.org" in text
        assert "no data licence" in text


# ================================================ a licence is not an access grant


class TestTheTwoLayersStaySeparate:
    def test_a_content_licence_does_not_grant_the_fetch(self) -> None:
        """Mission 1.18 established the separation for Stack Exchange, where the
        API Terms supplied the access grant the licence did not. TDF publishes no
        API terms, so the same rule cuts the other way for the first time."""
        text = document()
        assert "A content licence is not an access grant" in text
        assert "Mission 1.18" in text

    def test_the_licence_is_scoped_to_the_deployment_not_the_software(self) -> None:
        """§11. TDF states licences per property -- website 3.0, wiki 3.0
        Unported, Bugzilla 4.0 -- which is what makes the Bugzilla statement a
        statement about THIS data rather than a copied footer."""
        text = document()
        assert "CC BY-SA 3.0" in text
        assert "CC BY-SA 4.0" in text
        assert "copied a footer" in text


# ================================================== nothing was acquired


class TestNothingWasAcquired:
    def test_no_collector_exists_for_any_issue_tracker(self) -> None:
        """Asserted as an EQUALITY so a new collector cannot appear unnoticed."""
        from sros_acquisition import IMPLEMENTED_COLLECTORS

        assert set(IMPLEMENTED_COLLECTORS) == {
            "world-bank",
            "gdelt",
            "ted-eu",
            "stack-exchange",
            "wikimedia-pageviews",
        }

    def test_no_module_was_written_for_any_candidate(self) -> None:
        package = REPO_ROOT / "services/acquisition/python/sros_acquisition"
        for name in ("bugzilla", "launchpad", "documentfoundation"):
            assert not list(package.rglob(f"*{name}*.py")), name

    def test_no_record_kind_was_created_for_an_issue(self) -> None:
        """§19 would have applied only if an acquisition had happened. A
        registered kind with no data behind it is a promise the repository does
        not keep."""
        from sros_acquisition.normalization.model import RECORD_KINDS

        assert set(RECORD_KINDS) == {
            "numeric_observation",
            "lexical_frequency_observation",
            "procurement_notice",
            "community_question",
            "content_request_count",
        }

    def test_the_catalog_was_not_changed(self) -> None:
        """Neither candidate is registered, for the reason in this module's
        docstring. Pinned so that registering one later is a visible, deliberate
        act rather than a quiet one."""
        catalog = json.loads(CATALOG.read_text(encoding="utf-8"))
        ids = {s["source_id"] for s in catalog["sources"]}
        assert "documentfoundation-bugzilla" not in ids
        assert "launchpad-bugs" not in ids
        assert len(catalog["sources"]) == 29

    def test_the_probes_that_did_happen_are_disclosed(self) -> None:
        """A process failure, kept in the record rather than tidied away: two
        metadata-only probes reached TDF's `/rest/` BEFORE its robots directive
        was read. No request followed the reading, and nothing was persisted."""
        assert "process failure" in document().lower()


# ============================================ the architectural consequence


class TestWhatFollowsFromBeingBlocked:
    def test_the_route_is_blocked_by_governance_and_not_by_structure(self) -> None:
        """§32's exact distinction, and it decides what Mission 1.22 should be.

        If the relation had not existed, the answer would be "keep looking for a
        source". It exists in three trackers, so the deterministic routes are
        exhausted: text-derived identity failed in Missions 1.18 and 1.20, and
        source-native identity is unreachable here.
        """
        text = document()
        assert "The structure exists" in text
        assert "The access does not" in text

    def test_no_operator_was_contacted(self) -> None:
        """The repository may PREPARE a question and may never imply it asked
        one. No `OPERATOR_CORRESPONDENCE` evidence exists anywhere in the
        catalog, which is the tripwire Mission 1.15.4 installed."""
        catalog = json.loads(CATALOG.read_text(encoding="utf-8"))
        for entry in catalog["sources"]:
            for review in entry["reviews"]:
                for evidence in review.get("evidence") or ():
                    assert evidence["document_type"] != "OPERATOR_CORRESPONDENCE"
        assert "No message has been sent" in document()

    def test_no_inference_layer_was_started(self) -> None:
        """§33 and §38. Recommending Mission 1.22 is not beginning it."""
        nlp = REPO_ROOT / "services/nlp/python/sros_nlp"
        for name in ("inference", "equivalence", "similarity", "embedding"):
            assert not list(nlp.rglob(f"*{name}*.py")), name


def test_the_document_records_every_deployment_examined() -> None:
    """Five deployments were examined and all five are named, including the three
    that were not pursued. A landscape listing only a winner would make the next
    mission repeat the retrieval."""
    text = document()
    for name in ("TDF Bugzilla", "Launchpad", "Mozilla Bugzilla", "Debian BTS", "kernel.org"):
        assert name in text, name
