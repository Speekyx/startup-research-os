"""What authorises a resource, when the source names no licence.

Mission 1.9.1, H-28. `AuthorizedDataset` required a non-empty `licence`, and
GDELT grants use directly through its terms while naming no instrument:

    all datasets released by the GDELT Project are available for unlimited and
    unrestricted use for any academic, commercial or governmental use of any
    kind without fee

That is a broader grant than most licences give and it is not a licence. Every
way of filling the field -- "OTHER", "GDELT Terms Licence", "NONE", "N/A" --
puts an answer to *which licence?* in a place whose real answer is *that is the
wrong question for this source*, and lands a fabricated fact in the provenance
of every record it authorises.

**The half that matters most is §15**: a `DIRECT_GRANT` must not become a way
past a licence allowlist. World Bank's authorisation genuinely depends on that
allowlist, because its platform distributes under several licences and the wrong
one carries obligations nobody accepted.
"""

from __future__ import annotations

import pytest
from sros_acquisition.compliance import build_authorization, load_compliance
from sros_acquisition.compliance.config import AuthorizedDataset
from sros_acquisition.compliance.resources import ResourceDescriptor, authorize_resource
from sros_acquisition.registry.models import SourceRegistryError
from sros_contracts import ResourceContentOrigin, RightsBasis

from .conftest import REPO_ROOT

FABRICATIONS = ["OTHER", "GDELT Terms Licence", "GDELT licence", "NONE", "N/A", "unknown"]


@pytest.fixture(scope="session")
def compliance():
    return load_compliance(REPO_ROOT / "docs/data/source-compliance-v1.json")


def _dataset(**overrides) -> AuthorizedDataset:
    base = {
        "resource_id": "probe",
        "dataset_family": "probe-family",
        "content_origin": "PLATFORM_LICENSED",
        "basis": "a sentence quoting the document that authorised this",
    }
    return AuthorizedDataset(**{**base, **overrides})


class TestTheModelRefusesBothFabrications:
    def test_a_named_licence_resource_still_works(self) -> None:
        dataset = _dataset(rights_basis=RightsBasis.NAMED_LICENCE, licence="CC-BY-4.0")
        assert dataset.licence == "CC-BY-4.0"

    def test_a_direct_grant_resource_can_be_represented(self) -> None:
        """The whole point of H-28: expressible without inventing a licence."""
        dataset = _dataset(rights_basis=RightsBasis.DIRECT_GRANT)
        assert dataset.licence is None
        assert dataset.rights_basis is RightsBasis.DIRECT_GRANT

    def test_a_named_licence_with_no_identifier_is_refused(self) -> None:
        """The basis says a published instrument authorises this, so it has a name."""
        with pytest.raises(SourceRegistryError):
            _dataset(rights_basis=RightsBasis.NAMED_LICENCE)

    @pytest.mark.parametrize("fabrication", FABRICATIONS)
    def test_a_direct_grant_cannot_carry_an_invented_licence(self, fabrication) -> None:
        """The fabrication arriving through the other door.

        Enforcing only "NAMED_LICENCE needs a name" would leave every one of
        these writable under a direct grant, which is the exact failure the
        basis exists to prevent.
        """
        with pytest.raises(SourceRegistryError):
            _dataset(rights_basis=RightsBasis.DIRECT_GRANT, licence=fabrication)

    def test_there_is_no_unknown_basis_to_reach_for(self) -> None:
        """An unestablished basis is the ABSENCE of one, expressed as None and
        refused. A third enum member would be a value that looked like an
        answer."""
        assert {b.value for b in RightsBasis} == {"NAMED_LICENCE", "DIRECT_GRANT"}


class TestTheConfigLoaderRefusesSilence:
    def _load(self, tmp_path, dataset: dict):
        import json

        source = json.loads(
            (REPO_ROOT / "docs/data/source-compliance-v1.json").read_text(encoding="utf-8")
        )
        entry = next(s for s in source["sources"] if s["source_id"] == "world-bank")
        entry["datasets"] = [dataset]
        path = tmp_path / "compliance.json"
        path.write_text(json.dumps(source), encoding="utf-8")
        return load_compliance(path)

    def test_a_missing_basis_fails_rather_than_defaulting(self, tmp_path) -> None:
        """§28. Defaulting to NAMED_LICENCE would be correct for every entry
        that exists today and would silently mis-classify the first one that
        omitted it. A default is the opposite of failing."""
        with pytest.raises(SourceRegistryError, match="rights_basis"):
            self._load(
                tmp_path,
                {
                    "resource_id": "r",
                    "dataset_family": "f",
                    "licence": "CC-BY-4.0",
                    "content_origin": "PLATFORM_LICENSED",
                    "basis": "b",
                },
            )

    def test_an_unknown_basis_fails(self, tmp_path) -> None:
        with pytest.raises(SourceRegistryError, match="rights_basis"):
            self._load(
                tmp_path,
                {
                    "resource_id": "r",
                    "dataset_family": "f",
                    "content_origin": "PLATFORM_LICENSED",
                    "basis": "b",
                    "rights_basis": "PROBABLY_FINE",
                },
            )

    def test_every_committed_dataset_states_its_basis(self, compliance) -> None:
        for entry in compliance:
            for dataset in entry.datasets:
                assert dataset.rights_basis in set(RightsBasis), dataset.resource_id


class TestADirectGrantIsNotAWayPastALicenceAllowlist:
    """§15, and the reason this change needed tests before it needed features."""

    @pytest.fixture()
    def world_bank_scope(self, catalog, compliance):
        return build_authorization(catalog.get("world-bank"), compliance).resource_scope

    def _descriptor(self, scope, **overrides) -> ResourceDescriptor:
        base = {
            "source_id": "world-bank",
            "resource_id": "indicator/SP.POP.TOTL",
            "content_origin": ResourceContentOrigin.PLATFORM_LICENSED,
            "dataset_family": "indicators",
        }
        return ResourceDescriptor(**{**base, **overrides})

    def test_the_allowlist_still_admits_a_named_licence(self, world_bank_scope) -> None:
        """The control. A check that only ever denies would pass against a gate
        that denies everything."""
        result = authorize_resource(
            world_bank_scope,
            self._descriptor(
                world_bank_scope, rights_basis=RightsBasis.NAMED_LICENCE, licence="CC-BY-4.0"
            ),
        )
        assert result.allowed, result.denial_reasons

    def test_a_direct_grant_is_refused_by_a_licence_allowlist(self, world_bank_scope) -> None:
        """The rule §15 exists for. A direct grant is a real and often broader
        authorisation, and it is not a licence -- so it fails this scope rather
        than passing it by having nothing to compare."""
        result = authorize_resource(
            world_bank_scope,
            self._descriptor(world_bank_scope, rights_basis=RightsBasis.DIRECT_GRANT),
        )
        assert not result.allowed
        assert any("does not satisfy a licence allowlist" in r for r in result.denial_reasons)

    def test_a_direct_grant_carrying_a_licence_is_still_refused(self, world_bank_scope) -> None:
        """Belt and braces: even if a fabricated licence reached a descriptor by
        some route the config model does not allow, the basis still decides."""
        result = authorize_resource(
            world_bank_scope,
            self._descriptor(
                world_bank_scope, rights_basis=RightsBasis.DIRECT_GRANT, licence="CC-BY-4.0"
            ),
        )
        assert not result.allowed

    def test_an_unestablished_basis_is_refused(self, world_bank_scope) -> None:
        result = authorize_resource(
            world_bank_scope, self._descriptor(world_bank_scope, licence="CC-BY-4.0")
        )
        assert not result.allowed
        assert any("no established rights basis" in r for r in result.denial_reasons)

    def test_a_licence_outside_the_allowlist_is_refused_as_before(self, world_bank_scope) -> None:
        result = authorize_resource(
            world_bank_scope,
            self._descriptor(
                world_bank_scope,
                rights_basis=RightsBasis.NAMED_LICENCE,
                licence="License Specified Externally",
            ),
        )
        assert not result.allowed

    def test_the_basis_failure_is_distinguishable_from_a_missing_licence(
        self, world_bank_scope
    ) -> None:
        """Two different fixes. A reader chasing the wrong one loses an
        afternoon, which is why the refusals do not share a message."""
        wrong_basis = authorize_resource(
            world_bank_scope,
            self._descriptor(world_bank_scope, rights_basis=RightsBasis.DIRECT_GRANT),
        ).denial_reasons
        no_licence = authorize_resource(
            world_bank_scope,
            self._descriptor(world_bank_scope, rights_basis=RightsBasis.NAMED_LICENCE),
        ).denial_reasons
        assert wrong_basis != no_licence


class TestExistingSourcesAreUnaffected:
    def test_the_three_licensed_sources_still_authorise(self, catalog, compliance) -> None:
        """§15 and §16. The change must not have cost anything."""
        from sros_acquisition.compliance import AcquisitionNotAuthorizedError

        authorizable = []
        for source_id in ("world-bank", "eurostat", "gdelt"):
            try:
                build_authorization(catalog.get(source_id), compliance, environ={})
                authorizable.append(source_id)
            except AcquisitionNotAuthorizedError:
                pass
        assert authorizable == ["world-bank", "eurostat", "gdelt"]

    def test_world_bank_datasets_are_all_named_licence(self, compliance) -> None:
        entry = compliance.get("world-bank")
        assert entry.datasets
        for dataset in entry.datasets:
            assert dataset.rights_basis is RightsBasis.NAMED_LICENCE
            assert dataset.licence in {"CC-BY-4.0", "ODbL-1.0"}

    def test_the_world_bank_collector_carries_the_basis_into_its_descriptor(self) -> None:
        """The collector builds descriptors FROM the authorised dataset, never
        from what a caller claims. The basis has to travel that path too, or
        every World Bank resource would fail its own allowlist."""
        source = (
            REPO_ROOT / "services/acquisition/python/sros_acquisition/collection/world_bank.py"
        ).read_text(encoding="utf-8")
        assert "rights_basis=dataset.rights_basis" in source


class TestGdeltStillHasNoAuthorisedResource:
    """H-28 is closed, and Mission 1.9.2 filled the entry the model was holding.

    When this class was written, populating `datasets` meant deciding what one
    GDELT resource IS, and that depended on which DOC API mode the collector
    would use -- the question H-27 still cannot answer. Review 3 answered it
    from the other direction: the WEB-NGRAM files are a different route whose
    contract WAS observed, so the resources are the two ngram datasets and not a
    timeline mode. The class name is kept so the history stays readable.
    """

    def test_gdelt_resources_are_the_reviewed_ngram_datasets_and_no_api_mode(
        self, catalog, compliance
    ) -> None:
        """The entry is no longer empty, and it is still not a DOC API mode.

        H-27 remains open, so nothing on that route is authorised. What changed
        is that GDELT stopped being blocked ON H-27 for its first resource.
        """
        context = build_authorization(catalog.get("gdelt"), compliance)
        assert {d.resource_id for d in context.datasets} == {
            "web-ngrams/1gram",
            "web-ngrams/2gram",
        }
        assert not any("doc-api" in d.resource_id for d in context.datasets)

    def test_gdelt_carries_no_licence_anywhere(self, compliance) -> None:
        """The finding H-28 started from: GDELT names no instrument, and nothing
        in its configuration pretends otherwise."""
        entry = compliance.get("gdelt")
        assert entry.resource_scope.licence_allowlist is None
        assert not any(
            r.element.value == "LICENCE_IDENTIFIER" for r in entry.attribution.requirements
        )

    def test_a_gdelt_resource_would_be_a_direct_grant(self, compliance) -> None:
        """Constructed here rather than committed, because the resource model
        needs the mode decision. This asserts only that the MODEL can now hold
        it -- which is what H-28 was blocking."""
        dataset = _dataset(
            resource_id="doc-api/timeline-tone",
            dataset_family="DOC_API_TIMELINE_TONE",
            rights_basis=RightsBasis.DIRECT_GRANT,
            basis=(
                "GDELT's terms grant unlimited and unrestricted use for any academic, "
                "commercial or governmental use of any kind without fee, naming no licence"
            ),
        )
        assert dataset.licence is None
        assert dataset.rights_basis is RightsBasis.DIRECT_GRANT
