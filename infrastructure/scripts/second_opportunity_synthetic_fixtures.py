"""Synthetic fixtures for Mission 1.84.12's gates and tests: a packet, its names, and a good answer.

Nothing here is TED data, nothing is V3's answer, and nothing is sent anywhere. The packet, its
source, its registry names and its statements are written for these checks, in the shape the real
interpretation templates produce, so the real gate v1.3.0 and the real V4 runner stages can be run
over them. A synthetic answer passing is evidence that the machinery works on a well-formed answer,
never evidence about any model's answer.
"""

from __future__ import annotations

import json
from collections.abc import Mapping
from typing import Any

EVIDENCE = ("71717171-7171-4171-8171-717171717171", "72727272-7272-4272-8272-727272727272")
CLAIMS = ("a1a1a1a1-a1a1-4a1a-8a1a-a1a1a1a1a1a1", "a2a2a2a2-a2a2-4a2a-8a2a-a2a2a2a2a2a2")
SOURCE = "synthetic-notice-register"
NAME = "Notice Register Weekly (synthetic procurement register)"
SHORT_NAME = "Notice Register Weekly"
RESOURCE = "notices/synthetic-award-notices"
SUBJECT = "synthetic-notice-register:CPV-class:7777"
FAMILY = "public_procurement"
REQUEST_ID = "req_synthetic_mission_1_84_12"


def statements(name: str = NAME, source: str = SOURCE) -> dict[str, str]:
    """Two supplied statements, shaped as the interpretation templates write them."""
    return {
        CLAIMS[0]: (
            f'{name} reported that, in its "{RESOURCE}" resource, within a bounded set of 4 '
            '"CONTRACT_NOTICE" notices classified under "CPV" class "7777" (division "77"), the '
            'largest "TOTAL_VALUE" amount stated in "EUR" exceeded the smallest by 90000.'
        ),
        CLAIMS[1]: (
            f'The source "{source}" published, in its "{RESOURCE}" resource, at least one bounded '
            'set of "CONTRACT_NOTICE" notices classified under "CPV" class "7777" whose stated '
            '"TOTAL_VALUE" amounts in "EUR" differ from one another.'
        ),
    }


EVIDENCE_TO_CLAIM = dict(zip(EVIDENCE, CLAIMS, strict=True))


def packet(*, scoring: bool = True, extra: bool = False) -> Any:
    """The synthetic evidence packet. `extra` adds a row the approval boundary does not name."""
    from sros_opportunity import (
        EvidenceFacets,
        IndependenceState,
        PacketEligibility,
        ReliabilityStatus,
        build_packet,
    )
    from sros_opportunity.mapping import SIGNAL_DIMENSION_MAP

    mapping = SIGNAL_DIMENSION_MAP["procurement_value_contrast"]
    rows = list(zip(EVIDENCE, CLAIMS, strict=True))
    if extra:
        rows.append(EXTRA_ROW)
    eligibility = (
        PacketEligibility.ELIGIBLE_SCORING if scoring else PacketEligibility.ELIGIBLE_CONTEXT
    )
    facets = [
        EvidenceFacets(
            evidence_id=evidence_id,
            claim_id=claim_id,
            source_id=SOURCE,
            source_family=FAMILY,
            use_profile_id="local-private-research-v1",
            extraction_method="deterministic",
            claim_type="OBSERVED",
            claim_lifecycle="ACTIVE",
            claim_temporality="EVERGREEN",
            claim_origin="DETERMINISTIC_EXTRACTION",
            direction="SUPPORTS",
            observation_category="UNCATEGORISED",
            evidence_level=1,
            relevance=1.0,
            directness=1.0,
            extraction_confidence=1.0,
            reliability=0.5 if scoring else None,
            reliability_status=(
                ReliabilityStatus.RESOLVED
                if scoring
                else ReliabilityStatus.NO_APPLICABLE_ASSESSMENT
            ),
            independence_state=IndependenceState.UNKNOWN,
            independence_group_id=None,
            observed_at=None,
            signal_type_id="procurement_value_contrast",
            dimensions=mapping.dimensions,
            dimension_bound=mapping.bound,
        )
        for evidence_id, claim_id in rows
    ]
    return build_packet(None, SUBJECT, tuple((f, eligibility) for f in facets))


EXTRA_ROW = ("73737373-7373-4373-8373-737373737373", "a3a3a3a3-a3a3-4a3a-8a3a-a3a3a3a3a3a3")


def extra_statements() -> dict[str, str]:
    return {
        **statements(),
        EXTRA_ROW[1]: (
            f'{NAME} reported that, in its "{RESOURCE}" resource, within a bounded set of 4 '
            '"CONTRACT_NOTICE" notices classified under "CPV" class "7777" (division "77"), the '
            'largest "TOTAL_VALUE" amount stated in "EUR" exceeded the smallest by 90000.'
        ),
    }


def metadata(name: str = NAME, source: str = SOURCE) -> Any:
    """The source-metadata channel, from a synthetic registry entry."""
    from sros_opportunity.second_opportunity_gate_v1_3 import build_source_metadata_context

    return build_source_metadata_context(
        [
            {
                "source_id": source,
                "canonical_name": name,
                "datasets": [{"resource_id": RESOURCE, "name": "Synthetic award notices"}],
                "provenance": "a synthetic registry entry written for Mission 1.84.12's checks",
            }
        ]
    )


def mandatory_unsupported(evidence_packet: Any) -> list[str]:
    from sros_opportunity.synthesis import MANDATORY_UNSUPPORTED_REPORT

    return [d.value for d in MANDATORY_UNSUPPORTED_REPORT if d not in evidence_packet.dimensions]


def good_output(**changes: object) -> dict[str, Any]:
    """An answer that passes gate v1.3.0 and that the canonical OpportunityHypothesis accepts."""
    output: dict[str, Any] = {
        "decision": "FORM_HYPOTHESIS",
        "subject": SUBJECT,
        "target_actor_if_supported": (
            "Contracting authorities that published notices under CPV class 7777."
        ),
        "observed_need": (
            "The register records published notices with differing stated amounts; it does not "
            "establish a need."
        ),
        "candidate_intervention_class": (
            "No intervention class is supported; only an inquiry into the published notices "
            "could be scoped."
        ),
        "hypothesis_statement": (
            "One question worth testing is whether these authorities publish comparable notices "
            "again; nothing supplied establishes that they do."
        ),
        "supported_dimensions": ["BUYER_OR_BUDGET_EXISTENCE", "ECONOMIC_VALUE", "MARKET_ACTIVITY"],
        "unsupported_dimensions": mandatory_unsupported(packet()),
        "supporting_evidence_ids": list(EVIDENCE),
        "supporting_claim_ids": list(CLAIMS),
        "source_families": [FAMILY],
        "independence_status": "Independence is UNKNOWN for 2 of 2 rows.",
        "reliability_status": "Both rows are SCORABLE; no score exists.",
        "evidence_bound_reasoning_summary": (
            f"{SHORT_NAME} reported 4 notices under CPV class 7777 whose stated TOTAL_VALUE "
            "amounts differ by 90000 EUR, which is market activity in the bounded scope. The "
            "register does not establish willingness to pay or actual expenditure."
        ),
        "critical_uncertainties": ["Whether any authority publishes such notices again."],
        "commercial_claims_supported": [
            "Contracting authorities under CPV class 7777 published notices with stated amounts."
        ],
        "commercial_claims_not_supported": ["Buyers are willing to pay for software."],
        "recommended_next_evidence": ["Evidence of payments actually made under these notices."],
        "confidence_classification": "EXPLORATORY",
        "statement_classifications": [
            {
                "statement": "Notices under CPV class 7777 state differing amounts.",
                "classification": "OBSERVED_OR_EVIDENCE_SUPPORTED",
            },
            {
                "statement": "The same authority publishes such notices again.",
                "classification": "HYPOTHESIS_TO_VALIDATE",
            },
            {
                "statement": "An authority would pay for a new service.",
                "classification": "UNKNOWN_REQUIRES_EVIDENCE",
            },
        ],
    }
    output.update(changes)
    return output


def with_statement(statement: str, classification: str, **changes: object) -> dict[str, Any]:
    """The good answer with one more classified statement appended."""
    output = good_output(**changes)
    output["statement_classifications"] = [
        *output["statement_classifications"],
        {"statement": statement, "classification": classification},
    ]
    return output


def gate(
    output: Mapping[str, Any],
    *,
    evidence_packet: Any = None,
    supplied: Mapping[str, str] | None = None,
    names: Any = None,
) -> Any:
    """The real gate v1.3.0 over a synthetic answer."""
    from sros_opportunity.second_opportunity_gate_v1_2 import build_trusted_context
    from sros_opportunity.second_opportunity_gate_v1_3 import (
        evaluate_second_opportunity_output_v1_3,
    )

    chosen = evidence_packet if evidence_packet is not None else packet()
    return evaluate_second_opportunity_output_v1_3(
        output,
        chosen,
        dict(supplied if supplied is not None else statements()),
        {**EVIDENCE_TO_CLAIM, EXTRA_ROW[0]: EXTRA_ROW[1]},
        trusted_context=build_trusted_context(chosen),
        source_metadata=names if names is not None else metadata(),
    )


def response_body(output: Mapping[str, Any] | None, stop_reason: str = "tool_use") -> dict:
    """A provider response body in the Messages API shape, carrying `output` as the forced tool."""
    blocks: list[dict[str, Any]] = [{"type": "text", "text": "synthetic"}]
    if output is not None:
        blocks.append(
            {
                "type": "tool_use",
                "id": "toolu_synthetic",
                "name": "emit_structured_output",
                "input": dict(output),
            }
        )
    return {
        "id": "msg_synthetic",
        "type": "message",
        "role": "assistant",
        "model": "claude-sonnet-5",
        "content": blocks,
        "stop_reason": stop_reason,
        "usage": {"input_tokens": 11, "output_tokens": 22},
    }


def recorded_result(
    output: Mapping[str, Any] | None,
    *,
    stop_reason: str = "tool_use",
    request_id: str = REQUEST_ID,
) -> dict[str, Any]:
    """What the recording transport holds after one synthetic response: no socket was opened."""
    return {
        "response": None,
        "failure": None,
        "transport_responses": [
            {
                "status": 200,
                "body": json.dumps(response_body(output, stop_reason)),
                "headers": {"request-id": request_id},
            }
        ],
        "transport_errors": [],
        "telemetry": [],
        "timing": {"started_at": "synthetic", "finished_at": "synthetic", "elapsed_seconds": 0.0},
    }


def runner_context(
    *,
    evidence_packet: Any = None,
    supplied: Mapping[str, str] | None = None,
    names: Any = None,
    approved_evidence: tuple[str, ...] = EVIDENCE,
    approved_claims: tuple[str, ...] = CLAIMS,
) -> dict[str, Any]:
    """The context the V4 runner's stages read, for the synthetic packet."""
    from sros_opportunity.second_opportunity_gate_v1_2 import build_trusted_context

    chosen = evidence_packet if evidence_packet is not None else packet()
    pairs = {**EVIDENCE_TO_CLAIM, EXTRA_ROW[0]: EXTRA_ROW[1]}
    return {
        "packet_file": {
            "EXECUTION_PACKET_ID": "SECOND-OPPORTUNITY-SYNTH-EXEC-V4",
            "EXECUTION_PACKET_SHA256": "synthetic-preflight-digest",
            "SELECTED_PACKET_ID": chosen.packet_id,
            "PREPARATION_VERSION": "synthetic-preparation",
            "PROVIDER_ID": "anthropic",
            "MODEL_ID": "claude-sonnet-5",
            "PROMPT_VERSION": "1.3.0",
            "APPROVED_EVIDENCE_IDS": list(approved_evidence),
            "APPROVED_CLAIM_IDS": list(approved_claims),
            "APPROVED_EVIDENCE_TO_CLAIM": {e: pairs[e] for e in approved_evidence},
        },
        "packet": chosen,
        "statements": dict(supplied if supplied is not None else statements()),
        "evidence_to_claim": pairs,
        "trusted_context": build_trusted_context(chosen),
        "source_metadata": names if names is not None else metadata(),
        "representation": "synthetic-representation-digest",
        "prompt_hash": "synthetic-prompt-digest",
    }
