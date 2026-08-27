-- Canonical ontology values as INITIAL registry entries (Ontology V2 §14.3).
--
-- Deliberately small: only what validation and local development need. These
-- are rows, not enum values -- adding a product category later is an INSERT,
-- never a migration. Full registry population is Data Engineering work.
--
-- Idempotent.

INSERT INTO registry.registry_entries (registry, id, name, description) VALUES
    ('market_type',          'b2b',            'B2B',            'Business to business'),
    ('market_type',          'b2c',            'B2C',            'Business to consumer'),
    ('product_type',         'saas',           'SaaS',           'Software as a service'),
    ('product_type',         'game',           'Game',           'Game product'),
    ('user_motivation',      'problem',        'Problem',        'Solving a painful problem'),
    ('user_motivation',      'money',          'Money',          'Why the user acts: desire for financial gain (Ontology V2 §13)'),
    ('user_motivation',      'creativity',     'Creativity',     'Desire to create'),
    ('user_behavior',        'create',         'Create',         'The user makes something'),
    ('value_proposition',    'money_making',   'Money making',   'What the product provides: helps the user earn (Ontology V2 §13)'),
    ('value_proposition',    'money_saving',   'Money saving',   'Helps the user spend less'),
    ('value_proposition',    'time_saving',    'Time saving',    'Helps the user spend less time'),
    ('demand_signal_type',   'complaint',      'Complaint',      'Pain family'),
    ('demand_signal_type',   'explicit_request', 'Explicit request', 'Desire family'),
    ('retention_mechanism',  'habit',          'Habit',          'Recurring use'),
    ('monetization_model',   'subscription',   'Subscription',   'Recurring payment'),
    ('distribution_channel', 'seo',            'SEO',            'Organic search'),
    ('risk',                 'platform_dependency', 'Platform dependency', 'Depends on a third-party platform'),
    ('region',               'europe',         'Europe',         'Region identifier used by MarketScope REGION'),
    ('region',               'latam',          'Latin America',  'Region identifier used by MarketScope REGION')
ON CONFLICT (registry, id) DO NOTHING;
