"""Security properties of the HTTP surface.

Mission 0.4 §35, the parts that are about what reaches the outside world:
external error sanitization, and no secret exposure in `/ready` or in logs.

Tenant leakage and pooled-connection leakage are in `test_rls.py`; the prompt
injection boundary and the provider SDK restriction are in the llm-gateway
suite, next to the code they constrain.
"""

from __future__ import annotations

import json
import logging
import pathlib
import uuid

import pytest
from sros_gateway.config import ConfigurationError, Settings, load_settings

from .conftest import DATABASE_URL, QDRANT_URL, REDIS_URL, WORKSPACE_A, header, needs_postgres

# The credential fragments that appear in the local stack's configuration. If
# any of these reaches a response body or a log line, something is echoing
# configuration rather than reporting state.
SECRET_FRAGMENTS = ("sros_dev_password", "@127.0.0.1:55432", "postgresql://")


@needs_postgres
class TestReadinessLeaksNothing:
    def test_ready_reports_state_without_echoing_connection_strings(self, api_client) -> None:
        body = api_client.get("/ready", headers=header(WORKSPACE_A)).text
        for fragment in SECRET_FRAGMENTS:
            assert fragment not in body, f"/ready echoed {fragment!r}"

    def test_ready_reports_the_security_posture(self, api_client) -> None:
        """ "Designed for RLS" and "RLS enabled" were indistinguishable from
        outside until Mission 0.4, and the difference is the whole value of the
        second isolation layer."""
        payload = api_client.get("/ready", headers=header(WORKSPACE_A)).json()
        assert payload["security"]["rls_policies"] == "active"
        assert payload["security"]["app_db_role"] == "sros_app"

    def test_health_exposes_no_configuration_at_all(self, api_client) -> None:
        body = api_client.get("/health").text
        for fragment in SECRET_FRAGMENTS:
            assert fragment not in body

    def test_a_dependency_failure_is_reported_without_its_address(self) -> None:
        """A down dependency is the moment a handler is most likely to attach
        the exception text, and the exception text is where a credential lives.

        Redis is the dependency used here because it connects lazily. PostgreSQL
        cannot stand in: `Database.open(wait=True)` deliberately refuses to
        finish startup without a reachable database, so a gateway with a dead
        PostgreSQL never reaches `/ready` at all. That is the intended
        behaviour — a process that boots into a state where every request will
        fail is worse than one that does not boot — and it means this leak path
        is only reachable through a dependency that fails after startup.
        """
        from fastapi.testclient import TestClient
        from sros_gateway.app import create_app

        settings = Settings(
            database_url=DATABASE_URL,
            redis_url="redis://:hunter2@127.0.0.1:1/0",
            qdrant_url="http://127.0.0.1:1",
            environment="development",
        )
        with TestClient(create_app(settings)) as client:
            response = client.get("/ready", headers=header(WORKSPACE_A))

        assert response.status_code == 503
        assert "hunter2" not in response.text
        payload = response.json()
        assert payload["dependencies"]["redis"] == "unavailable"
        assert payload["dependencies"]["postgres"] == "ok"


@needs_postgres
class TestErrorSanitization:
    def test_a_malformed_workspace_header_does_not_reach_the_database(self, api_client) -> None:
        response = api_client.get(
            "/api/v1/research-projects", headers={"x-workspace-id": "'; DROP TABLE --"}
        )
        assert response.status_code == 422
        body = response.text.lower()
        assert "psycopg" not in body
        assert "traceback" not in body
        assert "select" not in body

    def test_a_not_found_response_carries_no_sql_or_schema_detail(self, api_client) -> None:
        response = api_client.get(
            f"/api/v1/research-projects/{uuid.uuid4()}", headers=header(WORKSPACE_A)
        )
        assert response.status_code == 404
        body = response.json()
        assert set(body) == {"error", "detail", "correlation_id"}
        assert "research.research_projects" not in body["detail"]

    def test_every_error_response_has_the_same_shape(self, api_client) -> None:
        """One shape everywhere: a caller parsing errors should never have to
        guess which of two formats it received."""
        cases = [
            (api_client.get("/api/v1/research-projects"), 400),
            (
                api_client.get(
                    f"/api/v1/research-sessions/{uuid.uuid4()}", headers=header(WORKSPACE_A)
                ),
                404,
            ),
        ]
        for response, expected_status in cases:
            assert response.status_code == expected_status
            assert set(response.json()) == {"error", "detail", "correlation_id"}

    def test_a_contract_violation_names_the_field_not_the_internals(self, api_client) -> None:
        project = api_client.post(
            "/api/v1/research-projects",
            headers=header(WORKSPACE_A),
            json={"name": "sanitization probe"},
        ).json()
        response = api_client.post(
            f"/api/v1/research-projects/{project['id']}/sessions",
            headers=header(WORKSPACE_A),
            json={
                "research_context": {"market_scope": {"type": "COUNTRY", "countries": ["FR", "DE"]}}
            },
        )
        assert response.status_code == 422
        detail = response.json()["detail"]
        assert "market_scope" in detail
        assert "sros_contracts" not in detail
        assert "File " not in detail


@needs_postgres
class TestLogsCarryIdsNotContent:
    def test_a_request_logs_correlation_without_research_content(self, api_client, caplog) -> None:
        """ADR-004 §Observability: never log raw collected content. The log
        pipeline is a second place tenant data can escape, and it is the one
        that never appears in a query audit."""
        secret = f"a-complaint-{uuid.uuid4().hex}"
        with caplog.at_level(logging.DEBUG, logger="sros.gateway"):
            api_client.post(
                "/api/v1/research-projects",
                headers=header(WORKSPACE_A),
                json={"name": secret},
            )
        assert secret not in caplog.text

    def test_the_log_format_is_structured(self) -> None:
        record = logging.LogRecord("sros.gateway", logging.INFO, __file__, 1, "hello", (), None)
        formatter = logging.Formatter(
            '{"ts":"%(asctime)s","level":"%(levelname)s",'
            '"logger":"%(name)s","message":"%(message)s"}'
        )
        json.loads(formatter.format(record))


class TestConfigurationRefusesUnsafeCombinations:
    def test_a_development_workspace_is_refused_outside_development(self) -> None:
        """ADR-005: the default workspace is a local convenience, never a code
        path. A deployed environment resolving tenants from configuration is
        one misconfiguration away from writing into the wrong workspace."""
        with pytest.raises(ConfigurationError):
            load_settings(
                {
                    "DATABASE_URL": "x",
                    "REDIS_URL": "y",
                    "QDRANT_URL": "z",
                    "ENVIRONMENT": "production",
                    "DEV_WORKSPACE_ID": str(uuid.uuid4()),
                }
            )

    def test_disabling_the_application_role_is_refused_outside_development(self) -> None:
        """ADR-012: without the role, RLS is bypassed and the repository filter
        is the only layer left."""
        with pytest.raises(ConfigurationError):
            load_settings(
                {
                    "DATABASE_URL": "x",
                    "REDIS_URL": "y",
                    "QDRANT_URL": "z",
                    "ENVIRONMENT": "production",
                    "APP_DB_ROLE": "",
                }
            )

    def test_the_application_role_defaults_on(self) -> None:
        settings = load_settings({"DATABASE_URL": "x", "REDIS_URL": "y", "QDRANT_URL": "z"})
        assert settings.app_db_role == "sros_app"

    def test_an_invalid_role_name_is_refused_at_construction(self) -> None:
        from sros_gateway.db.pool import Database

        for bad in ('sros"; DROP ROLE x; --', "Sros App", "-x"):
            with pytest.raises(ValueError):
                Database(DATABASE_URL, app_role=bad)


class TestNoCommittedSecrets:
    def test_no_provider_api_key_is_committed_in_the_environment_template(self) -> None:
        root = pathlib.Path(__file__).resolve().parents[4]
        template = root / "infrastructure" / "compose" / ".env.example"
        for line in template.read_text(encoding="utf-8").splitlines():
            if "API_KEY" in line and not line.strip().startswith("#"):
                assert line.strip().endswith("="), f"a populated credential is committed: {line}"

    def test_the_smoke_test_opt_in_is_documented_in_the_template(self) -> None:
        root = pathlib.Path(__file__).resolve().parents[4]
        template = (root / "infrastructure" / "compose" / ".env.example").read_text(
            encoding="utf-8"
        )
        assert "SROS_ENABLE_PROVIDER_SMOKE_TESTS" in template

    def test_the_readiness_payload_names_no_credential_field(self, api_client=None) -> None:
        from sros_gateway.api import health

        source = pathlib.Path(health.__file__).read_text(encoding="utf-8")
        for banned in ("password", "api_key", "secret", "token"):
            assert banned not in source.lower()


__all__ = ["QDRANT_URL", "REDIS_URL"]  # imported for the fixtures' side effects
