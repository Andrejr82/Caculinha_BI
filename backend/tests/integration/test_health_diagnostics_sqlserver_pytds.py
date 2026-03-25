import uuid
import asyncio

from fastapi.testclient import TestClient

from backend.main import app
from backend.app.api.v1.endpoints import diagnostics as diagnostics_endpoint
from backend.app.api.v1.endpoints import health as health_endpoint


class AdminUser:
    def __init__(self):
        self.id = uuid.uuid4()
        self.username = "admin-user"
        self.email = "admin@example.com"
        self.role = "admin"
        self.is_active = True


def test_diagnostics_config_and_status_report_sqlserver_pytds(monkeypatch):
    monkeypatch.setattr(diagnostics_endpoint.settings, "CHAT_STATE_BACKEND", "sqlserver")
    monkeypatch.setattr(diagnostics_endpoint.settings, "USE_SQL_SERVER", False)
    monkeypatch.setattr(diagnostics_endpoint.settings, "REDIS_ENABLED", False)
    monkeypatch.setattr(
        diagnostics_endpoint.settings,
        "DATABASE_URL",
        "mssql+pytds://u:p@localhost:1433/Projeto_Caculinha",
    )
    monkeypatch.setattr(
        diagnostics_endpoint.settings,
        "PARQUET_DATA_PATH",
        str((__import__("pathlib").Path(__file__).resolve().parents[3] / "backend" / "data" / "parquet" / "admmat.parquet")),
    )

    config_body = asyncio.run(
        diagnostics_endpoint.get_db_config(current_user=AdminUser())
    ).model_dump()
    assert config_body["use_sql_server"] is True
    assert config_body["chat_state_backend"] == "sqlserver"
    assert config_body["database_server"] == "localhost"
    assert config_body["database_name"] == "Projeto_Caculinha"
    assert config_body["database_user"] == "u"
    assert config_body["database_driver"] == "mssql+pytds"

    status_body = asyncio.run(
        diagnostics_endpoint.get_db_status(current_user=AdminUser())
    )
    assert status_body["sql_server"]["status"] == "enabled"
    assert status_body["sql_server"]["runtime_mode"] == "sqlserver_pytds"
    assert status_body["parquet"]["analytics_source"] == "parquet"
    assert status_body["redis"]["status"] == "disabled"


def test_diagnostics_test_connection_supports_pytds(monkeypatch):
    monkeypatch.setattr(diagnostics_endpoint.settings, "CHAT_STATE_BACKEND", "sqlserver")
    monkeypatch.setattr(diagnostics_endpoint.settings, "USE_SQL_SERVER", False)
    monkeypatch.setattr(
        diagnostics_endpoint.settings,
        "DATABASE_URL",
        "mssql+pytds://u:p@localhost:1433/Projeto_Caculinha",
    )
    monkeypatch.setattr(
        diagnostics_endpoint,
        "_test_connection_pytds",
        lambda: diagnostics_endpoint.ConnectionTestResult(
            success=True,
            message="Conexão pytds estabelecida com sucesso!",
            version="SQL Server 2022",
            tables=["chat_conversations", "chat_messages"],
        ),
    )

    body = asyncio.run(
        diagnostics_endpoint.test_sql_connection(current_user=AdminUser())
    ).model_dump()
    assert body["success"] is True
    assert body["version"] == "SQL Server 2022"
    assert "chat_conversations" in body["tables"]


def test_health_check_reports_database_connected_via_pytds(monkeypatch):
    monkeypatch.setattr(health_endpoint.settings, "CHAT_STATE_BACKEND", "sqlserver")
    monkeypatch.setattr(health_endpoint.settings, "USE_SQL_SERVER", False)
    monkeypatch.setattr(health_endpoint.settings, "REDIS_ENABLED", False)
    monkeypatch.setattr(
        health_endpoint.settings,
        "DATABASE_URL",
        "mssql+pytds://u:p@localhost:1433/Projeto_Caculinha",
    )
    async def _fake_check_database():
        return {
            "status": "healthy",
            "message": "Database connected via pytds",
        }

    async def _fake_check_data_adapter():
        return {
            "status": "healthy",
            "source": "parquet",
            "message": "Parquet file accessible",
        }

    monkeypatch.setattr(health_endpoint, "check_database", _fake_check_database)
    monkeypatch.setattr(health_endpoint, "check_data_adapter", _fake_check_data_adapter)
    monkeypatch.setattr(
        health_endpoint,
        "check_environment",
        lambda: {
            "status": "healthy",
            "message": "Environment configured",
        },
    )
    health_endpoint._last_health_check["timestamp"] = 0
    health_endpoint._last_health_check["status"] = None

    body = asyncio.run(health_endpoint.health_check())
    assert body["status"] == "healthy"
    assert body["analytics_source"] == "parquet"
    assert body["chat_state_backend"] == "sqlserver"
    assert body["checks"]["database"]["message"] == "Database connected via pytds"
    assert body["checks"]["redis"]["status"] == "disabled"


def test_root_health_reports_parquet_first_runtime(monkeypatch):
    monkeypatch.setattr(app.state, "chat_state_backend", "sqlserver_pytds", raising=False)
    monkeypatch.setattr(app.state, "redis_enabled", False, raising=False)
    client = TestClient(app)

    response = client.get("/health")
    assert response.status_code == 200
    body = response.json()
    assert body["analytics_source"] == "parquet"
    assert body["chat_state_backend"] == "sqlserver_pytds"
    assert body["redis_enabled"] is False
