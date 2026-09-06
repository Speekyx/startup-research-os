# Mission 1.74.4 — The designated address bounced, and a replacement is prepared

Generated from `globalping-r2-replacement-recipient-review-v1.json` and `globalping-r2-enquiry-packet-v2.json`. Do not edit by hand.

## What the provider's own documents say

| surface | addresses | designates for |
|---|---|---|
| Terms of Use, section 16 Contact Us | `legal@globalping.io` | questions about these Terms |
| Privacy Policy, section 12 Contact Us | `legal@globalping.io` | questions about this Privacy Policy |
| Cookie Policy, How to contact us | `legal@globalping.io` | the Data Protection Team |
| website footer, committed source | `d@globalping.io` | general contact |
| rendered homepage footer | `d@globalping.io` | general contact |

the provider's own current documents designate an address that does not accept mail, while a different address is published and live on its homepage. This record does not resolve that: it is a fact about the provider's published channels, and it is not evidence that the general address is answered, monitored or appropriate for a Terms question.

## The address is established, and it is not a designation

- established first-party: **True**
- read from committed source rather than a rendered shell: **True**
- accepted because it was supplied: **False**
- is it the Terms-designated channel: **False**
- the Terms-designated channel remains: `legal@globalping.io`

**`ESTABLISHED_FIRST_PARTY_GENERAL_CONTACT_NOT_THE_TERMS_DESIGNATED_CHANNEL`**

three provider documents designate legal@globalping.io and that address rejected delivery, so the designated route is unreachable. The general contact channel is the only other address the provider publishes, which makes it the remaining first-party route to the same organisation -- a weaker basis than a designation, and the record says so rather than promoting it.

Mission 1.65 established that a recipient is judged on provenance rather than on spelling: a string rule would have refused a correctly established address while still admitting a guessed one that happened to look ordinary. An unusual local part read off a first-party page is established; a conventional one nobody published is not.

## What this does not establish

- that d@globalping.io is monitored, or answered
- that it is an appropriate channel for a Terms question
- that legal@globalping.io is permanently dead rather than temporarily rejecting
- that the provider intends the footer address to replace the designated one

The designated address is recorded as `OPERATOR_ATTESTED_DELIVERY_REJECTED_ONCE` and explicitly not as `PERMANENTLY_NONEXISTENT`. one rejected attempt, attested by a person, does not establish that an address does not exist. What is recorded is what happened once.

## The replacement packet

| | v1 | v2 |
|---|---|---|
| recipient | `legal@globalping.io` | `d@globalping.io` |
| channel | `PROVIDER_DESIGNATED_TERMS_CHANNEL` | `PROVIDER_PUBLISHED_GENERAL_CONTACT_CHANNEL` |
| subject | identical | identical |
| body | identical | identical |
| digest | `713d62c91ac56934…` | `987f3ff57ce661c6…` |
| send status | `NOT_AUTHORIZED` | `NOT_AUTHORIZED` |

a line explaining that the designated address bounced was considered and NOT added. The operator's instruction was to preserve the approved text unless a change is strictly required, and nothing about the question changes with the recipient. Adding prose would make this a differently worded enquiry that the operator has not read.

v1 went to the address the Terms designate for Terms questions. This one goes to the address the provider publishes for general contact. Reusing the v1 label would assert a designation this address does not have.

## The earlier approval is spent

the Mission 1.74.2 approval binds approved_content_sha256, and this packet's digest differs because the recipient and channel differ. So the exhausted approval cannot name this document -- the hash is what defeats the hazard of a shared question_id, rather than a rule somebody has to remember.

**No approval covers this packet.** A new recipient is a new action and needs a new explicit operator approval.
