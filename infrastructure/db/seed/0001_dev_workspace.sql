-- Development seed. Idempotent. NEVER applied to a non-development database.
--
-- ADR-005: the default development workspace is a convenience for local work,
-- NEVER a code path. No service, repository or task may fall back to it when
-- workspace_id is missing -- a missing workspace_id is an error in every
-- environment.
--
-- A SECOND workspace is seeded on purpose: integration tests must be able to
-- assert tenant isolation, and a suite with one workspace cannot detect a
-- missing tenant filter.

INSERT INTO core.users (id, email, display_name)
VALUES ('00000000-0000-4000-8000-000000000002', 'dev@localhost', 'Local Developer')
ON CONFLICT (id) DO NOTHING;

INSERT INTO core.workspaces (id, slug, name)
VALUES
    ('00000000-0000-4000-8000-000000000001', 'dev', 'Development Workspace'),
    ('00000000-0000-4000-8000-000000000003', 'dev-other', 'Second Workspace (isolation tests)')
ON CONFLICT (id) DO NOTHING;

INSERT INTO core.workspace_memberships (workspace_id, user_id, role)
VALUES
    ('00000000-0000-4000-8000-000000000001', '00000000-0000-4000-8000-000000000002', 'owner'),
    ('00000000-0000-4000-8000-000000000003', '00000000-0000-4000-8000-000000000002', 'owner')
ON CONFLICT (workspace_id, user_id) DO NOTHING;
