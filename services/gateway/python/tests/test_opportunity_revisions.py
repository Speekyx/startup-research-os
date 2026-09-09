"""Mission 1.78. Opportunity revisions are append-only, and the newest one is current.

`research.opportunity_hypothesis_revisions` has no explicit current pointer: the current
revision is the highest `revision` for an Opportunity, which is what the canonical index
`(workspace_id, opportunity_id, revision DESC)` exists for. These tests hold that model
relationally, so they pass on an empty CI database and on a deployment carrying revisions --
a test pinned to "revision 2 exists" would assert that no deployment may ever be fresh.

Nothing is written. The `database` fixture is read through directly.
"""

from __future__ import annotations

import pytest

from tests.conftest import needs_postgres

pytestmark = needs_postgres

WORKSPACE_ID = "00000000-0000-4000-8000-000000000001"


def _rows(database, query, params=()):
    with database.connection() as conn, conn.transaction():
        conn.execute("SELECT set_config('app.workspace_id', %s, true)", (WORKSPACE_ID,))
        cur = conn.execute(query, params)
        columns = [d[0] for d in cur.description]
        return [dict(zip(columns, r, strict=True)) for r in cur.fetchall()]


class TestRevisionsAreAppendOnlyAndTheNewestIsCurrent:
    def test_revisions_are_contiguous_from_one(self, database) -> None:
        for opportunity in _rows(database, "SELECT id FROM research.opportunities"):
            numbers = [
                r["revision"]
                for r in _rows(
                    database,
                    "SELECT revision FROM research.opportunity_hypothesis_revisions"
                    " WHERE opportunity_id = %s ORDER BY revision",
                    (opportunity["id"],),
                )
            ]
            assert numbers == list(range(1, len(numbers) + 1))

    def test_the_current_reader_returns_the_highest_revision(self, database) -> None:
        for opportunity in _rows(database, "SELECT id FROM research.opportunities"):
            newest = _rows(
                database,
                "SELECT id, revision FROM research.opportunity_hypothesis_revisions"
                " WHERE opportunity_id = %s ORDER BY revision DESC LIMIT 1",
                (opportunity["id"],),
            )
            highest = _rows(
                database,
                "SELECT max(revision) AS revision FROM research.opportunity_hypothesis_revisions"
                " WHERE opportunity_id = %s",
                (opportunity["id"],),
            )[0]["revision"]
            assert newest[0]["revision"] == highest

    def test_the_historical_reader_returns_revision_one_exactly_once(self, database) -> None:
        for opportunity in _rows(database, "SELECT id FROM research.opportunities"):
            first = _rows(
                database,
                "SELECT * FROM research.opportunity_hypothesis_revisions"
                " WHERE opportunity_id = %s AND revision = 1",
                (opportunity["id"],),
            )
            assert len(first) == 1
            assert first[0]["epistemic_limitations"]

    def test_a_later_revision_keeps_the_hypothesis_fields_of_the_first_unless_a_model_wrote_it(
        self, database
    ) -> None:
        """A deterministic revision (no model version) is a reconciliation and may not
        change what the hypothesis asserts."""
        for opportunity in _rows(database, "SELECT id FROM research.opportunities"):
            revisions = _rows(
                database,
                "SELECT * FROM research.opportunity_hypothesis_revisions"
                " WHERE opportunity_id = %s ORDER BY revision",
                (opportunity["id"],),
            )
            for previous, current in zip(revisions, revisions[1:], strict=False):
                if current["model_version"] is not None:
                    continue
                for field in ("hypothesis_statement", "target_actor", "candidate_intervention"):
                    assert current[field] == previous[field]
                assert current["epistemic_limitations"]

    def test_every_revision_link_names_an_existing_evidence_row_of_the_same_workspace(
        self, database
    ) -> None:
        orphans = _rows(
            database,
            "SELECT l.id FROM research.opportunity_hypothesis_evidence l"
            " LEFT JOIN scoring.evidence e ON e.id = l.evidence_id AND e.workspace_id = l.workspace_id"
            " WHERE e.id IS NULL",
        )
        assert orphans == []

    def test_a_scoring_eligible_citation_resolves_a_reliability_late(self, database) -> None:
        """ELIGIBLE_SCORING at citation is a claim that the row had a resolved reliability.
        The stored column is NULL by design, so the claim is checked against the current
        assessments through lineage rather than against the column."""
        cited = _rows(
            database,
            "SELECT l.evidence_id, l.eligibility_at_citation, e.source_id, c.claim_type,"
            " c.proposition_facts ->> 'proposition' AS kind,"
            " (SELECT array_agg(DISTINCT r.provenance ->> 'resource_id') FROM nlp.signal_inputs si"
            "   JOIN acquisition.raw_records r ON r.id = si.raw_record_id"
            "  WHERE si.signal_id = e.signal_id) AS resources,"
            " (SELECT array_agg(DISTINCT si.record_kind_id) FROM nlp.signal_inputs si"
            "  WHERE si.signal_id = e.signal_id) AS kinds"
            " FROM research.opportunity_hypothesis_evidence l"
            " JOIN scoring.evidence e ON e.id = l.evidence_id"
            " JOIN research.claims c ON c.id = e.claim_id",
        )
        assessments = _rows(
            database,
            "SELECT source_id, resource_id, record_kind_id, claim_type, proposition_kind"
            " FROM epistemic.reliability_assessments WHERE superseded_at IS NULL",
        )
        current = {
            (
                a["source_id"],
                a["resource_id"],
                a["record_kind_id"],
                a["claim_type"],
                a["proposition_kind"],
            )
            for a in assessments
        }
        for row in cited:
            resources = [r for r in (row["resources"] or []) if r]
            kinds = [k for k in (row["kinds"] or []) if k]
            scope = (
                (row["source_id"], resources[0], kinds[0], row["claim_type"], row["kind"])
                if len(resources) == 1 and len(kinds) == 1
                else None
            )
            if row["eligibility_at_citation"] == "ELIGIBLE_SCORING":
                assert scope in current, row["evidence_id"]


if __name__ == "__main__":
    pytest.main([__file__])
