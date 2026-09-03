"""Mission 1.39 §34. Render the convergence contract registry deterministically.

**Generated from the registry, never hand-written beside it.** Two copies of one
fact drift, and the drift is discovered by whoever trusted the wrong one (ADR-009
applied to documentation). Mission 1.36.1 found exactly that: a packet nobody
regenerated, carrying values the contract would have refused.

**Unlike the calibration feasibility audit, this one belongs in CI.** It renders
repository code into a repository file and touches no database, so an empty
deployment changes nothing about it -- which is the distinction Mission 1.37
recorded when it explained why its own audit could not be a CI step.

Usage:

    uv run python infrastructure/scripts/render_convergence_contract.py
    uv run python infrastructure/scripts/render_convergence_contract.py --check
"""

from __future__ import annotations

import argparse
import json
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "packages" / "claim-model" / "python"))
sys.path.insert(0, str(ROOT / "packages" / "contracts" / "python"))

OUT = ROOT / "docs" / "data" / "proposition-convergence-contract-v1.json"

# The seven propositions that existed before Mission 1.39 and that convergence
# must not reach. Listed by name so a new contract for one of them shows up as a
# diff in this file rather than as a surprise in a later mission.
HISTORICAL_PROPOSITION_KINDS = (
    "source_reported_metric_period_change",
    "platform_counted_content_request_change",
    "community_site_published_questions_carrying_tag",
    "community_site_questions_without_accepted_answer",
    "source_reported_term_frequency_change",
    "source_reported_term_frequency_contrast",
    "source_reported_procurement_value_contrast",
)


def build() -> dict:
    from sros_claim_model import CONVERGENCE_CONTRACTS, contract_for
    from sros_claim_model.convergence import (
        ObservationOverlap,
        QualificationOutcome,
        SourceBoundary,
    )

    return {
        "$comment": (
            "Mission 1.39 §34. GENERATED from sros_claim_model.convergence by "
            "infrastructure/scripts/render_convergence_contract.py; edit the registry, not "
            "this file, and re-render. A convergence-enabled proposition kind declares WHICH "
            "facts decide the assertion and WHICH decide the witness, before any observation "
            "is processed. Convergence defined as 'drop fields until the hashes match' is a "
            "coincidence with a procedure, not a contract."
        ),
        "artifact_version": "proposition-convergence-contract@1.0.0",
        "generated_by": "mission-1.39",
        "outcome": "PROPOSITION_CONVERGENCE_CONTRACT_READY",
        "claim_type_policy": {
            "permitted": ["OBSERVED"],
            "why": (
                "An OBSERVED claim asserts what a source reported, attributed, and an "
                "existential over a publication is a faithful restatement: a reader can go "
                "and read it there, and it stays true if the source was wrong. An INFERRED "
                "convergence would need the interpretation layer docs/CLAUDE.md records as "
                "deliberately unbuilt, and the constructor refuses one so it cannot be built "
                "here by accident."
            ),
            "refused_reasoning_steps": [
                "generalising from samples",
                "estimating prevalence",
                "asserting the class usually behaves this way",
                "combining source meanings",
                "inferring a latent phenomenon",
            ],
        },
        "source_boundary_policy": {
            "values": [m.value for m in SourceBoundary],
            "v1_rule": "SAME_SOURCE_AND_RESOURCE",
            "why": (
                "Attribution is part of an OBSERVED proposition. 'Wikimedia counted X' and "
                "'TED reported Z' are different propositions with different falsifiers, and "
                "rendering them into similar English does not make them one. No cross-source "
                "member exists in the enum: a member nobody may pass is an invitation."
            ),
            "source_id_is_always_identity": True,
        },
        "identity_versus_witness_rule": {
            "test": (
                "If changing field F changes WHAT the Claim asserts, F is proposition "
                "identity. If changing F only changes WHICH observation witnesses the same "
                "assertion, F may be witness identity."
            ),
            "witness_facts_are_retained": (
                "A witness fact stays on the Signal, on the Evidence and in provenance. It "
                "stops being an identity; it does not stop existing."
            ),
            "unclassified_facts_are_refused": (
                "qualify() refuses a fact set carrying a fact the contract classifies as "
                "neither. The key is built from whatever is in the mapping, so a fact nobody "
                "placed is a fact that decides."
            ),
        },
        "qualification_predicate": {
            "outcomes": [m.value for m in QualificationOutcome],
            "inputs": ["the persisted proposition facts", "the Signal type id"],
            "forbidden_mechanisms": [
                "embeddings",
                "cosine or any vector similarity",
                "LLM equivalence",
                "fuzzy string matching",
                "semantic clustering",
                "SAME_PROBLEM_FAMILY",
            ],
            "why_three_valued": (
                "'this observation is not about that proposition' and 'this observation did "
                "not carry the facts to tell' are different situations, and only the second "
                "is fixable upstream."
            ),
        },
        "overlap_semantics": {
            "values": [m.value for m in ObservationOverlap],
            "is_not_independence": True,
            "why": (
                "DISJOINT says two witnesses read different records. It does not say the two "
                "Evidence rows are independent corroboration: they can still share the "
                "publisher, the collection mechanism, the methodology and the population. "
                "independence_state stays UNKNOWN and the conservative unknown-provenance "
                "collapse remains authoritative."
            ),
            "member_name_collision_avoided": (
                "ObservationOverlap uses UNESTABLISHED rather than UNKNOWN, because "
                "EvidenceIndependenceState already has UNKNOWN and two vocabularies sharing "
                "a member name is how a mapping between them gets written by accident."
            ),
        },
        "duplicate_witness_policy": {
            "rule": "two Evidence rows on one Claim must have different witness keys",
            "witness_key": "proposition_key over the witness facts, namespaced by proposition kind",
            "why_not_uuids": (
                "a guard comparing generated ids would agree that the same cohort inserted "
                "twice is two witnesses"
            ),
        },
        "temporality_handling": {
            "rule": "declared on the contract, never inferred from the observation",
            "this_contract": "EVERGREEN",
            "why": (
                "H-37 is open: a TED notice publishes an offset without a time, so the source "
                "establishes no instant this claim could be bounded by. An existential over a "
                "publication needs none -- once witnessed, it stays witnessed."
            ),
        },
        "scope_handling": {
            "rule": (
                "a convergent proposition carries its own ObservationScope, derived at packet "
                "build time from the identifiers it holds, exactly as Mission 1.34 specified. "
                "Different scopes do not converge because the statement template matches."
            ),
            "multi_scope_architecture_changed": False,
        },
        "backward_compatibility": {
            "historical_proposition_kinds": list(HISTORICAL_PROPOSITION_KINDS),
            "kinds_with_a_convergence_contract": [
                kind for kind in HISTORICAL_PROPOSITION_KINDS if contract_for(kind) is not None
            ],
            "guarantee": (
                "proposition_key is unchanged and was not touched. Convergence computes the "
                "same hash over a smaller mapping, which is what a different fact set has "
                "always produced. No historical template changed, no historical key changed, "
                "and convergence is opt-in per proposition kind."
            ),
        },
        "production_wiring": {
            "wired_into_the_claim_interpretation_job": False,
            "why": (
                "Mission 1.39 settles the contract. Until a later mission decides to run it "
                "against live records, no Signal in this deployment can witness two Claims, "
                "so the double-counting boundary is enforced by absence rather than by a rule."
            ),
        },
        "contracts": [contract.to_json() for contract in CONVERGENCE_CONTRACTS.values()],
        "forbidden_convergence_examples": [
            {
                "example": "two Wikimedia articles on the same day",
                "facts_differing": ["content_id"],
                "why_refused": (
                    "platform_counted_content_request_change has no convergence contract, and "
                    "if it did, content_id would be identity: merging them merges Docker with "
                    "Podman, which Mission 1.38 measured as twelve real claim pairs one field "
                    "apart"
                ),
            },
            {
                "example": "a TED observation and a World Bank observation",
                "facts_differing": ["source_id"],
                "why_refused": "source_id is always identity for an OBSERVED claim",
            },
            {
                "example": "two cohorts in different CPV divisions",
                "facts_differing": ["classification_division"],
                "why_refused": "the division is what the assertion is about",
            },
            {
                "example": "a DIFFERS cohort and an EQUAL cohort",
                "facts_differing": ["relation"],
                "why_refused": "two assertions, not two readings of one",
            },
            {
                "example": "the same cohort processed twice",
                "facts_differing": [],
                "why_refused": (
                    "identical witness key. Replay is idempotent and adds no Evidence row"
                ),
            },
        ],
        "test_fixtures": {
            "contract_and_near_misses": (
                "packages/claim-model/python/tests/test_proposition_convergence.py"
            ),
            "persistence_and_aggregation": (
                "services/nlp/python/tests/test_proposition_convergence_persistence.py"
            ),
            "all_fixtures_are_synthetic": True,
            "written_to_a_disposable_workspace": True,
        },
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", help="compare and write nothing")
    args = parser.parse_args()

    rendered = json.dumps(build(), indent=2, ensure_ascii=False) + "\n"

    if args.check:
        if not OUT.exists():
            print(f"REFUSED: {OUT.name} does not exist; run without --check first")
            return 1
        if OUT.read_text(encoding="utf-8") == rendered:
            print(f"ok       {OUT.name} matches the registry")
            return 0
        print(f"DRIFT    {OUT.name} does not match the registry; re-render it")
        return 1

    OUT.write_text(rendered, encoding="utf-8")
    print(f"wrote {OUT.name}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
