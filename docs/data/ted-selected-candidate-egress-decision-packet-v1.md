# Decision packet TED-EGRESS-OPPSYNTH-V1

Generated from `ted-selected-candidate-egress-decision-packet-v1.json`. Do not edit by hand.

**Version 1**, digest `f27c34460f413def15c260e72fd2261a1fba666b574e9e2ee60bf7ef38a39577`.

THIS DOCUMENT RECORDS NO APPROVAL. That is a statement about this document and never a statement that no approval exists; if one is given it is recorded beside this packet, not inside it, so the bytes the operator read do not change when they answer

## The question

- source `ted-eu`
- use profile `local-private-research-v1`
- activity `external_model_transmission`
- processing purpose: bounded external inference for Opportunity hypothesis synthesis
- subject `ted-eu:CPV-class:9261`, "Sports facilities operation services"
- representation `opportunity-transmission-representation@1.0.0`, 5 claims, 3604 characters, digest `2528a56a4a9e873bfd04662aeb52916eb80faafe10ab085e716cbdcee77c5b72`

## What is not in it

- `RAW_TED_PAYLOAD_INCLUDED` = false
- `PERSONAL_DATA_INCLUDED` = false
- `NOTICE_BODY_INCLUDED` = false
- `TRAINING` = false
- `FINE_TUNING` = false
- `EMBEDDINGS` = false
- `PUBLIC_REDISTRIBUTION` = false
- `CUSTOMER_SOURCE_DATA_ACCESS` = false

## Held authority

- Commission Decision 2011/833/EU, Articles 1-13, read in full 2026-08-31 and re-retrieved 2026-09-04. Article 3(2) defines reuse by purpose and enumerates no acts
- Publications Office written reply, case 2026-COP-201, 2026-09-04: reuse permitted for commercial and non-commercial purposes provided the source is acknowledged; the database-copyright question should not prevent reuse; retrieval method is not relevant
- TED and SIMAP legal notice, re-inspected 2026-09-04
- TED Developer Docs, Search API, 2026-08-31
- TED Open Data Service, 2026-08-31
- ted-eu local-private-research-v1 review v3: model_processing PERMITTED, external_model_transmission NOT_ASSESSED, redistribution NOT_PERMITTED
- operator acceptance of ted-database-right-residual-exposure-accepted, verifier_version ted-v3-official-reuse-acknowledgement-v1, scoped in its own words to bounded queries

## Finding

Three of ADR-033's four gates are already open: a model may read this material, the profile permits this class of egress, and the provider posture is APPROVED on its own contract text. The fourth was never asked. The held authority supports the act without settling it: reuse is purpose-framed and act-free, the publisher has said in writing that commercial reuse is permitted and that the database-copyright question should not prevent it, and the object that would leave carries no TED text, no notice payload and no personal data. What remains is not a documentary gap. It is a reading of an instrument that names no acts, and the scope of an acceptance the operator wrote for bounded queries.

## Conditions

1. PURPOSE-BOUND. The permission, if given, covers bounded external inference for Opportunity hypothesis synthesis and no other processing purpose. A different purpose is a different assessment.
2. REPRESENTATION-BOUND. Only the payload whose digest this packet names may be transmitted, under opportunity-transmission-representation@1.0.0: canonical subject and canonical Claims only, allowlisted keys, no raw notice, no notice body, no API response, no personal data. A payload that exceeds it is refused rather than trimmed.
3. PROVIDER-BOUND, BY PROPERTY AND NOT BY NAME. Transmission only to a provider whose reviewed posture is APPROVED in the provider policy register: its own terms commit, for the API route this deployment would use, that submitted content is not used to train its models, and its retention posture is documented and bounded. No vendor is named here, because a source review states the property a provider must have and the provider register decides which providers have it. A provider approval is not a source permission and this condition does not make it one.
4. NO TRAINING, NO FINE-TUNING, NO EMBEDDINGS. Each stays exactly as unassessed as it is today, and this decision widens none of them.
5. NO REDISTRIBUTION, NO RESALE, NO CUSTOMER-FACING ACCESS. Unchanged, and the condition whose breach would move the use to commercial-multi-tenant-research-v1, which is REQUIRES_REVIEW.
6. ACKNOWLEDGEMENT. Article 6(2)(a) as asserted by the publisher's reply. Already satisfied as a property of the payload, because every Claim statement names the source in its own wording, and it travels to any derived output that restates a TED-derived proposition.
7. NO DISTORTION. Article 6(2)(b). A generated hypothesis must not restate these propositions as realised expenditure, willingness to pay, demand or market size.
8. SUBJECT-BOUND FOR THIS PACKET. This decision names one packet. Whether it generalises to other TED packets under the same representation and purpose is a question the operator may answer explicitly; it is not assumed either way here.

## Open questions

- H-36A: whether a sui generis database right subsists in the TED corpus, and who would hold it. NOT ESTABLISHED in either direction, and this decision does not resolve it.
- Whether the Re-use Decision's purpose-framed grant reaches onward transmission to a processor. The instrument names no acts, so it neither permits nor prohibits this one.
- Whether the operator's acceptance of the residual database-right exposure, written for bounded queries through the authorised routes, extends to a transmission that reaches a new counterparty. Only the operator can answer this, and it is the reason this packet exists.
- Whether this repository's derived propositions engage any TED right at all. Nothing in the payload is a TED document, and 'nothing engages' is a conclusion no held document states.

## Options

| option | means | cost |
|---|---|---|
| **PERMIT_WITH_EXACT_CONDITIONS** | external_model_transmission becomes PERMITTED_WITH_CONDITIONS for this source, profile, purpose and representation, recorded by appending a review successor in a separate mission that verifies this digest first | appending a review version orphans the v3 condition verifications, including the HUMAN_CONFIRMATION acceptance, so TED becomes ineligible until the operator records it again. That cost is stated here rather than discovered afterwards |
| **DEFER** | external_model_transmission stays NOT_ASSESSED and the candidate's synthesis route stays closed. Nothing else changes and no other work is blocked by it | the selected candidate cannot reach synthesis, which is the only thing it is for |
| **REFUSE** | external_model_transmission becomes NOT_PERMITTED for this source and profile, recorded as a decision rather than as an open question | a refusal is a decision an operator can revisit and is materially different from silence, which is why it is offered as an option rather than left as the default |

No option is defaulted. no option is defaulted; a packet that recommended one would be making the decision.

the packet id and version, the source, the profile, the activity, the purpose, the subject, the packet id, the representation schema and digest and boundary, the five negative states, the conditions, the held authority and the open questions, plus the option NAMES. It excludes itself, the preparation date and the option prose, so recording an approval beside this packet does not move it and re-wording an option's explanation cannot pass unnoticed as a re-hash of the same decision.
