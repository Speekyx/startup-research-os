-- 0033 — a document that has no URL, and the rule that made it unstorable
--
-- `OPERATOR_CORRESPONDENCE` has been a permitted `document_type` since
-- migration 0004, and `source-registry-v1.md` §1 names operator correspondence
-- as one of the three kinds of authoritative evidence an approval may rest on.
-- No row has ever carried it. Mission 1.15.4 §32 installed a tripwire asserting
-- that, so the first one would be a deliberate act with a real document behind
-- it, and Mission 1.45 is that act: a written reply from the Publications
-- Office's Head of Sector for Copyright, answering a clarification request about
-- reuse of TED data.
--
-- IT COULD NOT BE STORED. `document_url` is NOT NULL and constrained to
-- `^https?://`, enforced again in `PolicyEvidence.__post_init__`. A letter has
-- no URL. So the enum permitted a class of evidence the URL rule refused, and
-- the refusal was invisible because nobody had tried.
--
-- THE RULE'S OWN JUSTIFICATION DOES NOT REACH IT. The model states the reason:
-- "an assessment that cannot be re-opened cannot be re-verified when the
-- platform changes its terms". That is an argument about PUBLISHED PAGES, which
-- change under a stable address. Correspondence is the opposite kind of thing:
-- it is fixed at the moment it was sent, it cannot be silently amended, and it
-- is re-verified by producing the message rather than by fetching it again.
-- Requiring an http address of it does not make it more re-openable; it makes it
-- unrecordable.
--
-- THE REPAIR IS THE NARROWEST ONE THAT KEEPS THE GUARANTEE. A correspondence or
-- legal-review row may address itself with a `mailto:` locator -- for TED that
-- is `op-copyright@publications.europa.eu`, the functional mailbox the TED legal
-- notice itself publishes and the address the request was sent to, so the matter
-- can be re-opened by quoting its case identifier back to it -- and it must then
-- carry a `document_fingerprint`. BOTH HALVES OR NEITHER: a locator with no
-- fingerprint names a mailbox rather than a document, and a fingerprint with no
-- locator names bytes nobody can ask about. Every other evidence type is
-- untouched and still requires http(s).
--
-- WHAT IS NOT CHANGED. `document_fingerprint` is not made mandatory for the
-- http(s) types: a published page is identified by its address, and demanding a
-- hash of one would force a re-fetch to prove a row is still valid. And nothing
-- here stores the document. The excerpt cap stands, so this remains a reference
-- with a checksum and never a mirror of somebody's letter.

ALTER TABLE registry.source_policy_evidence
    DROP CONSTRAINT source_policy_evidence_url_check;

ALTER TABLE registry.source_policy_evidence
    ADD CONSTRAINT source_policy_evidence_url_check
        CHECK (
            document_url ~ '^https?://'
         OR (
                document_type IN ('OPERATOR_CORRESPONDENCE', 'LEGAL_REVIEW')
            AND document_url ~ '^mailto:[^[:space:]@]+@[^[:space:]@]+$'
            AND document_fingerprint IS NOT NULL
            AND length(btrim(document_fingerprint)) > 0
            )
        );

COMMENT ON COLUMN registry.source_policy_evidence.document_url IS
    'Where the document is addressed. An absolute http(s) URL for anything a '
    'publisher serves. A `mailto:` locator is permitted ONLY for '
    'OPERATOR_CORRESPONDENCE and LEGAL_REVIEW, which have no address to fetch, '
    'and only together with a document_fingerprint -- the locator says how the '
    'matter is re-opened, the fingerprint says which document was read.';

COMMENT ON COLUMN registry.source_policy_evidence.document_fingerprint IS
    'A checksum of the exact artifact read. Optional for published pages, which '
    'are identified by their address and legitimately change. REQUIRED for a '
    'mailto-addressed correspondence or legal review, because there is no '
    'address to re-fetch and the bytes are the only thing that can be checked.';
