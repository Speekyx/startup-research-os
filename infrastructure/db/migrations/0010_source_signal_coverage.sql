-- =============================================================================
-- 0010_source_signal_coverage.sql -- what could be LEARNED from a source
--
-- Mission 1.7. Governed by docs/data/source-coverage-gap-analysis-v1.md (written
-- before this file, per §47) and ADR-017.
--
-- WHAT THIS ADDS, AND WHY IT IS NOT source_capabilities
--
-- `source_capabilities` says what DATA comes back: `reviews`, `ratings`,
-- `vote-counts`. This says what could be LEARNED from it. The two are different
-- relations and neither determines the other -- `reviews` evidences PROBLEM on
-- a support forum, DESIRE on a wishlist and ENTERTAINMENT on a games store, from
-- the identical capability. Merging them would give one column two meanings and
-- the second would be inferred from the first by whoever read it next.
--
-- WHAT IS DELIBERATELY REUSED
--
-- Ontology V2 §3.4's seventeen user behaviours are exactly the seventeen
-- Mission 1.7 §5 asks for, so behaviour coverage introduces NO new vocabulary
-- and references `user_behavior` directly. Migration 0004 seeded one of the
-- seventeen as an illustration; the other sixteen are canonical per §14.3 and
-- are loaded here. `user_motivation` is in the same state: three of seventeen.
--
-- WHAT IS NEW, AND WHY IT COULD NOT BE REUSED
--
-- Eleven of the sixteen signal families Mission 1.7 §4 names are already
-- `user_motivation` entries, by name and by meaning. They are NOT reused
-- directly: `user_motivation` describes why a PERSON wants something, and a
-- source does not have a motivation. Instead `signal_family` records, per entry,
-- the canonical entry it projects -- so the correspondence is data rather than a
-- coincidence of spelling. Four entries map to nothing and say so.
--
-- WHAT THIS MUST NEVER BECOME (§35, §36, D-03)
--
-- There is no weight, no score and no confidence column here, and adding one
-- would be a per-source reliability coefficient under another name. Coverage is
-- POTENTIAL, never permission: a source may cover ENTERTAINMENT and be
-- PROHIBITED, and nothing in this file joins the two.
--
-- Forward-only. Never edited after it has been applied anywhere.
-- =============================================================================

-- -----------------------------------------------------------------------------
-- 1. registry_entries learns to point at another registry entry
--
-- Nullable, and nullable on purpose: TREND, COMMERCIAL, COMMUNITY and
-- DEVELOPER_ACTIVITY have no canonical counterpart, and forcing them to a
-- near-match would corrupt the vocabulary they were pushed into. NULL is the
-- honest answer and is the reason this cannot be a NOT NULL column.
-- -----------------------------------------------------------------------------
ALTER TABLE registry.registry_entries
    ADD COLUMN maps_to_registry TEXT,
    ADD COLUMN maps_to_id       TEXT,
    ADD CONSTRAINT registry_entries_maps_to_fkey
        FOREIGN KEY (maps_to_registry, maps_to_id)
        REFERENCES registry.registry_entries (registry, id),
    -- Both or neither. Half a reference is a dangling pointer that reads as one.
    ADD CONSTRAINT registry_entries_maps_to_complete_check
        CHECK ((maps_to_registry IS NULL) = (maps_to_id IS NULL)),
    -- An entry mapping to itself would be a cycle of length one and would make
    -- "follow the projection" non-terminating for whoever wrote the query.
    ADD CONSTRAINT registry_entries_maps_to_not_self_check
        CHECK (maps_to_registry IS DISTINCT FROM registry OR maps_to_id IS DISTINCT FROM id);

COMMENT ON COLUMN registry.registry_entries.maps_to_registry IS
    'The canonical vocabulary this entry projects, or NULL where none exists. '
    'Introduced for signal_family (ADR-017); available to any registry.';

-- -----------------------------------------------------------------------------
-- 2. The canonical user_behavior entries (Ontology V2 §3.4)
--
-- Not new vocabulary: these are the ontology's own initial entries, sixteen of
-- which were never loaded. §14.3 authorises adding registry entries without an
-- ontology change, and these were already canonical.
-- -----------------------------------------------------------------------------
INSERT INTO registry.registry_entries (registry, id, name, description) VALUES
    ('user_behavior', 'discover',    'Discover',    'Finding something previously unknown to the user'),
    ('user_behavior', 'consume',     'Consume',     'Reading, watching or listening without producing'),
    ('user_behavior', 'play',        'Play',        'Playing a game or engaging in play for its own sake'),
    ('user_behavior', 'learn',       'Learn',       'Acquiring a skill or body of knowledge'),
    ('user_behavior', 'compare',     'Compare',     'Evaluating options against one another'),
    ('user_behavior', 'predict',     'Predict',     'Forecasting an outcome, competitively or otherwise'),
    ('user_behavior', 'collect',     'Collect',     'Accumulating items, sets or achievements'),
    ('user_behavior', 'share',       'Share',       'Passing something on to others'),
    ('user_behavior', 'compete',     'Compete',     'Measuring oneself against others'),
    ('user_behavior', 'customize',   'Customize',   'Personalising an artefact, avatar or environment'),
    ('user_behavior', 'track',       'Track',       'Recording and monitoring something over time'),
    ('user_behavior', 'discuss',     'Discuss',     'Conversing, asking and answering in public'),
    ('user_behavior', 'buy',         'Buy',         'Purchasing'),
    ('user_behavior', 'sell',        'Sell',        'Offering something for sale'),
    ('user_behavior', 'collaborate', 'Collaborate', 'Working with others on a shared artefact'),
    ('user_behavior', 'automate',    'Automate',    'Delegating a repeated task to software')
ON CONFLICT (registry, id) DO NOTHING;

-- -----------------------------------------------------------------------------
-- 3. The canonical user_motivation entries (Ontology V2 §3.3)
--
-- Fourteen of seventeen were never loaded. Same authority as §2 above.
-- -----------------------------------------------------------------------------
INSERT INTO registry.registry_entries (registry, id, name, description) VALUES
    ('user_motivation', 'utility',         'Utility',         'The user wants a task done'),
    ('user_motivation', 'entertainment',   'Entertainment',   'The user wants to be entertained'),
    ('user_motivation', 'curiosity',       'Curiosity',       'The user wants to know'),
    ('user_motivation', 'learning',        'Learning',        'The user wants to become able'),
    ('user_motivation', 'competition',     'Competition',     'The user wants to win or rank'),
    ('user_motivation', 'social',          'Social',          'The user wants to interact with others'),
    ('user_motivation', 'expression',      'Expression',      'The user wants to be seen as themselves'),
    ('user_motivation', 'status',          'Status',          'The user wants standing among others'),
    ('user_motivation', 'discovery',       'Discovery',       'The user wants to find something new'),
    ('user_motivation', 'emotion',         'Emotion',         'The user wants to feel something'),
    ('user_motivation', 'achievement',     'Achievement',     'The user wants to complete or master'),
    ('user_motivation', 'collection',      'Collection',      'The user wants to complete a set'),
    ('user_motivation', 'personalization', 'Personalization', 'The user wants it to be theirs'),
    ('user_motivation', 'experience',      'Experience',      'The user wants to have lived it')
ON CONFLICT (registry, id) DO NOTHING;

-- -----------------------------------------------------------------------------
-- 4. Three more source families (§34)
--
-- The existing eleven have no home for Steam, Twitch or OpenAlex. A family is a
-- DISCOVERY attribute and never an eligibility one -- §34 is explicit, and the
-- gate does not read this column.
-- -----------------------------------------------------------------------------
INSERT INTO registry.registry_entries (registry, id, name, description) VALUES
    ('source_family', 'gaming',    'Gaming platform',  'Game stores, launchers and their player-facing data'),
    ('source_family', 'creator',   'Creator platform', 'Platforms where individuals publish and are followed'),
    ('source_family', 'knowledge', 'Knowledge base',   'Encyclopaedic, scholarly and reference corpora')
ON CONFLICT (registry, id) DO NOTHING;

-- -----------------------------------------------------------------------------
-- 5. signal_family (§4, ADR-017)
--
-- Sixteen entries. Eleven project a canonical user_motivation; five record NULL
-- rather than a near-match -- four because no canonical counterpart exists, and
-- DESIRE because its counterpart is a CLOSED ENUM that the pointer structurally
-- cannot reference.
--
-- These say what a source COULD expose. They do not say the source is eligible,
-- they carry no evidence weight, and they do not enter EvidenceScore.
-- -----------------------------------------------------------------------------
INSERT INTO registry.registry_entries
        (registry, id, name, description, maps_to_registry, maps_to_id) VALUES
    ('signal_family', 'problem',            'Problem',
     'Stated difficulties, complaints, workarounds and unmet needs',
     'user_motivation', 'problem'),
    -- Corresponds to the DESIRE demand signal family (Ontology V2 §3.6), which
    -- is a CLOSED ENUM and therefore has no registry_entries row to point at.
    -- The projection can only reference a registry, so this is NULL: the
    -- correspondence is real and is recorded in prose because the mechanism
    -- structurally cannot hold it. Inventing a `demand_signal_family` registry
    -- to make the pointer resolve would reclassify a closed enum as extensible,
    -- which is a material ontology change and not this migration's to make.
    ('signal_family', 'desire',             'Desire',
     'Wants and requests stated without a problem behind them. Corresponds to '
     'the closed demand signal family DESIRE (Ontology V2 §3.6)',
     NULL, NULL),
    ('signal_family', 'entertainment',      'Entertainment',
     'What people watch, play and consume for enjoyment',
     'user_motivation', 'entertainment'),
    ('signal_family', 'creativity',         'Creativity',
     'What people make, remix and publish',
     'user_motivation', 'creativity'),
    ('signal_family', 'curiosity',          'Curiosity',
     'What people look up and read about',
     'user_motivation', 'curiosity'),
    ('signal_family', 'competition',        'Competition',
     'Ranking, scoring, contests and comparative performance',
     'user_motivation', 'competition'),
    ('signal_family', 'social',             'Social',
     'Interaction between people: replies, follows, mentions',
     'user_motivation', 'social'),
    ('signal_family', 'discovery',          'Discovery',
     'How people find things that are new to them',
     'user_motivation', 'discovery'),
    ('signal_family', 'learning',           'Learning',
     'Study, instruction, questions asked in order to become able',
     'user_motivation', 'learning'),
    ('signal_family', 'collection',         'Collection',
     'Accumulating, completing sets, tracking owned items',
     'user_motivation', 'collection'),
    ('signal_family', 'personalization',    'Personalization',
     'Customising artefacts, avatars, profiles and environments',
     'user_motivation', 'personalization'),
    ('signal_family', 'status',             'Status',
     'Standing, reputation, badges, follower counts',
     'user_motivation', 'status'),
    -- The four with no canonical counterpart. NULL is the finding, not a gap
    -- somebody forgot to fill in.
    ('signal_family', 'community',          'Community',
     'Group formation, belonging and sustained participation',
     NULL, NULL),
    ('signal_family', 'trend',              'Trend',
     'Change over time: growth, decline, seasonality, emergence',
     NULL, NULL),
    ('signal_family', 'commercial',         'Commercial',
     'Purchase intent, pricing, monetisation and market activity',
     NULL, NULL),
    ('signal_family', 'developer_activity', 'Developer activity',
     'What builders adopt, publish and depend on',
     NULL, NULL)
ON CONFLICT (registry, id) DO NOTHING;

-- -----------------------------------------------------------------------------
-- 6. registry.source_signal_coverage
--
-- Many-valued, so a column on registry.sources was never an option: it would
-- force one value, or an array with no referential integrity to the vocabulary.
--
-- `basis` is NOT NULL for the same reason a retention override records one
-- (source-registry-v1.md §6). A coverage row with no stated justification cannot
-- be re-checked when the source changes, and is indistinguishable from somebody
-- having wanted the category filled in.
-- -----------------------------------------------------------------------------
CREATE TABLE registry.source_signal_coverage (
    id                  UUID        PRIMARY KEY,
    source_id           TEXT        NOT NULL REFERENCES registry.sources (id) ON DELETE CASCADE,

    signal_registry     TEXT        NOT NULL DEFAULT 'signal_family',
    signal_family       TEXT        NOT NULL,

    -- Which documented capability or data this rests on. Prose, addressed to a
    -- reviewer who has to decide whether it still holds.
    basis               TEXT        NOT NULL,
    notes               TEXT,
    created_at          TIMESTAMPTZ NOT NULL DEFAULT now(),

    CONSTRAINT source_signal_coverage_unique UNIQUE (source_id, signal_family),
    CONSTRAINT source_signal_coverage_registry_check
        CHECK (signal_registry = 'signal_family'),
    CONSTRAINT source_signal_coverage_basis_not_blank_check
        CHECK (length(btrim(basis)) > 0),
    CONSTRAINT source_signal_coverage_family_fkey
        FOREIGN KEY (signal_registry, signal_family)
        REFERENCES registry.registry_entries (registry, id)
);

CREATE INDEX idx_source_signal_coverage_family
    ON registry.source_signal_coverage (signal_family);

COMMENT ON TABLE registry.source_signal_coverage IS
    'What kinds of opportunity signal a source COULD expose (Mission 1.7 §4). '
    'Potential, never permission: a covered source may be PROHIBITED. Carries '
    'no weight, no score and no confidence -- that would be D-03 by the back '
    'door (§35).';

-- -----------------------------------------------------------------------------
-- 7. registry.source_behavior_coverage
--
-- References `user_behavior` directly. No new vocabulary: Ontology V2 §3.4 is
-- already exactly the list Mission 1.7 §5 asks for.
-- -----------------------------------------------------------------------------
CREATE TABLE registry.source_behavior_coverage (
    id                  UUID        PRIMARY KEY,
    source_id           TEXT        NOT NULL REFERENCES registry.sources (id) ON DELETE CASCADE,

    behavior_registry   TEXT        NOT NULL DEFAULT 'user_behavior',
    behavior            TEXT        NOT NULL,

    basis               TEXT        NOT NULL,
    notes               TEXT,
    created_at          TIMESTAMPTZ NOT NULL DEFAULT now(),

    CONSTRAINT source_behavior_coverage_unique UNIQUE (source_id, behavior),
    CONSTRAINT source_behavior_coverage_registry_check
        CHECK (behavior_registry = 'user_behavior'),
    CONSTRAINT source_behavior_coverage_basis_not_blank_check
        CHECK (length(btrim(basis)) > 0),
    CONSTRAINT source_behavior_coverage_behavior_fkey
        FOREIGN KEY (behavior_registry, behavior)
        REFERENCES registry.registry_entries (registry, id)
);

CREATE INDEX idx_source_behavior_coverage_behavior
    ON registry.source_behavior_coverage (behavior);

COMMENT ON TABLE registry.source_behavior_coverage IS
    'Which canonical user behaviours (Ontology V2 §3.4) a source records '
    'evidence of. Reuses user_behavior rather than defining a second '
    'behaviour vocabulary (Mission 1.7 §5).';

-- -----------------------------------------------------------------------------
-- 8. Grants
--
-- Global reference data like everything else in `registry` (ADR-012 §4): no
-- workspace_id, no policy, SELECT only at runtime. Coverage is administered
-- through the catalog and the CLI, which connect as the migration role.
-- -----------------------------------------------------------------------------
GRANT SELECT ON registry.source_signal_coverage,
                registry.source_behavior_coverage
    TO sros_app;
