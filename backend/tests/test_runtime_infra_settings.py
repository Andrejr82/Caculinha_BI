from pathlib import Path

from backend.app.config.settings import Settings
from backend.app.core.utils.session_manager import SessionManager
from backend.app.config.settings import settings as global_settings


def test_runtime_paths_are_resolved_to_absolute_paths():
    configured = Settings(
        SECRET_KEY="x" * 32,
        DATABASE_URL="",
        USE_SQL_SERVER=False,
        RUNTIME_STORAGE_ROOT="data/runtime",
        CHAT_STATE_DB_PATH="data/runtime/chat_state/agentbi.db",
        VECTOR_DB_PATH="data/runtime/chat_state/conversation_vectors.duckdb",
        SESSION_LEGACY_STORAGE_PATH="data/runtime/sessions",
        ATTACHMENTS_STORAGE_PATH="data/runtime/attachments",
    )

    assert Path(configured.RUNTIME_STORAGE_ROOT).is_absolute()
    assert Path(configured.CHAT_STATE_DB_PATH).is_absolute()
    assert Path(configured.VECTOR_DB_PATH).is_absolute()
    assert Path(configured.SESSION_LEGACY_STORAGE_PATH).is_absolute()
    assert Path(configured.ATTACHMENTS_STORAGE_PATH).is_absolute()


def test_session_manager_uses_configured_runtime_paths(monkeypatch, tmp_path: Path):
    db_path = tmp_path / "runtime" / "chat_state" / "agentbi.db"
    sessions_path = tmp_path / "runtime" / "sessions"

    monkeypatch.setattr(global_settings, "CHAT_STATE_DB_PATH", str(db_path))
    monkeypatch.setattr(global_settings, "SESSION_LEGACY_STORAGE_PATH", str(sessions_path))

    assert SessionManager.default_db_path() == db_path
    assert SessionManager.default_storage_dir() == sessions_path

    manager = SessionManager()
    assert manager.db_path == db_path
    assert manager.storage_dir == sessions_path


def test_session_manager_switches_to_sqlserver_backend_when_enabled(monkeypatch):
    monkeypatch.setattr(global_settings, "CHAT_STATE_BACKEND", "sqlserver")
    monkeypatch.setattr(global_settings, "USE_SQL_SERVER", True)
    monkeypatch.setattr(global_settings, "PYODBC_CONNECTION_STRING", "DRIVER={ODBC Driver 17 for SQL Server};SERVER=test;DATABASE=test;UID=u;PWD=p;")
    monkeypatch.setattr(global_settings, "DATABASE_URL", "mssql+aioodbc://u:p@test:1433/test?driver=ODBC+Driver+17+for+SQL+Server")

    manager = SessionManager()
    assert manager.backend == "sqlserver"


def test_session_manager_switches_to_sqlserver_pytds_backend_when_database_url_uses_pytds(monkeypatch):
    monkeypatch.setattr(global_settings, "CHAT_STATE_BACKEND", "sqlserver")
    monkeypatch.setattr(global_settings, "USE_SQL_SERVER", False)
    monkeypatch.setattr(global_settings, "DATABASE_URL", "mssql+pytds://u:p@test:1433/test")
    monkeypatch.setattr(global_settings, "PYODBC_CONNECTION_STRING", "")

    manager = SessionManager()
    assert manager.backend == "sqlserver_pytds"
