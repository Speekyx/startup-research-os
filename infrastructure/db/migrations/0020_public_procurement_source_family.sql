-- =============================================================================
-- 0020_public_procurement_source_family.sql -- a family for sources whose
-- primary record is a completed purchase
--
-- Mission 1.15. Governed by docs/data/source-registry-v1.md and
-- docs/data/demand-side-source-expansion-v1.md.
--
-- WHY A NEW FAMILY
--
-- Every existing family describes what a source PUBLISHES ABOUT: economic
-- statistics, news, community discussion, applications, games. Public
-- procurement records something none of them do -- that a named buyer paid a
-- named supplier a stated amount for stated work.
--
-- That distinction is the whole reason Mission 1.15 registered these sources.
-- WILLINGNESS_TO_PAY has been the portfolio's largest missing evidence family
-- since Mission 1.7, and every candidate for it so far could only ever have
-- evidenced a LISTED PRICE. A contract award notice is a TRANSACTION, and the
-- two are not degrees of the same thing: a price on a page is what somebody
-- asked for, and an award is what somebody paid.
--
-- Filing these under `economic_data` would have hidden exactly that. World Bank
-- and Eurostat publish aggregate statistics ABOUT economies; TED publishes
-- individual purchases. A family that covered both would make the coverage
-- report say the portfolio has had commercial evidence since Mission 1.5, which
-- it has not.
--
-- WHAT THIS GRANTS
--
-- Nothing. A family is a vocabulary entry; it says what KIND of thing a source
-- is and carries no permission, no coverage claim and no weight. Both sources
-- registered under it are REQUIRES_REVIEW.
--
-- Forward-only. Never edited after it has been applied anywhere.
-- =============================================================================

INSERT INTO registry.registry_entries (registry, id, name, description) VALUES
    ('source_family', 'public_procurement', 'Public procurement',
     'Official records of public bodies buying goods and services: contract '
     'notices and award notices naming the buyer, the supplier and the value. '
     'The primary record is a completed purchase, which is what separates this '
     'family from economic_data -- statistics ABOUT an economy rather than '
     'individual transactions within it.')
ON CONFLICT (registry, id) DO NOTHING;
