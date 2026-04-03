import json
import logging
import os
import sqlite3
import threading
import uuid
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional

from backend.app.config.settings import settings

logger = logging.getLogger(__name__)


class SessionManager:
    @staticmethod
    def default_db_path() -> Path:
        return Path(settings.CHAT_STATE_DB_PATH)

    @staticmethod
    def default_storage_dir() -> Path:
        return Path(settings.SESSION_LEGACY_STORAGE_PATH)

    def __init__(
        self,
        storage_dir: str = "data/sessions",
        db_path: Optional[str] = None,
        history_limit: int = 20,
        tenant_id: str = "default",
    ):
        resolved_storage_dir = Path(storage_dir) if storage_dir != "data/sessions" else self.default_storage_dir()
        self.storage_dir = resolved_storage_dir
        self.storage_dir.mkdir(parents=True, exist_ok=True)
        self.db_path = Path(db_path) if db_path else self.default_db_path()
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self.history_limit = max(1, int(history_limit))
        self.tenant_id = str(tenant_id or "default").strip() or "default"
        self._lock = threading.RLock()
        self._initialized = False
        self.backend = self._resolve_backend()

    def _is_sqlserver_backend(self) -> bool:
        return self.backend in {"sqlserver", "sqlserver_pytds"}

    def _resolve_backend(self) -> str:
        if settings.CHAT_STATE_BACKEND == "sqlserver":
            database_url = str(getattr(settings, "DATABASE_URL", "") or "").strip()
            if database_url.startswith("mssql+pytds://"):
                return "sqlserver_pytds"
            if (
                settings.USE_SQL_SERVER
                and str(getattr(settings, "PYODBC_CONNECTION_STRING", "") or "").strip()
            ):
                return "sqlserver"
        return "sqlite"

    def _validate_session_id(self, session_id: str) -> None:
        try:
            uuid.UUID(session_id)
            return
        except ValueError:
            if not str(session_id or "").isalnum():
                logger.error(
                    "Invalid session_id format (potential path traversal): '%s' (Len: %s, Type: %s)",
                    session_id,
                    len(str(session_id)),
                    type(session_id),
                )
                raise ValueError("Invalid session_id format")

    def _get_file_path(self, session_id: str) -> Path:
        self._validate_session_id(session_id)
        return self.storage_dir / f"{session_id}.json"

    def _get_connection(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path, check_same_thread=False)
        conn.row_factory = sqlite3.Row
        return conn

    def _get_sqlserver_connection(self):
        if self.backend == "sqlserver_pytds":
            import pytds
            from sqlalchemy.engine import make_url

            url = make_url(str(settings.DATABASE_URL))
            return pytds.connect(
                dsn=url.host or "localhost",
                port=int(url.port or 1433),
                database=url.database,
                user=url.username,
                password=url.password,
                cafile=None,
                validate_host=False,
                enc_login_only=False,
            )

        import pyodbc

        conn = pyodbc.connect(settings.PYODBC_CONNECTION_STRING)
        return conn

    def _sqlserver_execute(self, cursor, query: str, *params):
        if self.backend == "sqlserver_pytds":
            query = query.replace("?", "%s")
        if params:
            return cursor.execute(query, tuple(params))
        return cursor.execute(query)

    def _ensure_initialized(self) -> None:
        if self._is_sqlserver_backend():
            self._ensure_initialized_sqlserver()
            return
        if self._initialized:
            return

        with self._lock:
            if self._initialized:
                return

            conn = self._get_connection()
            try:
                conn.executescript(
                    """
                    CREATE TABLE IF NOT EXISTS conversations (
                        id TEXT PRIMARY KEY,
                        tenant_id TEXT NOT NULL,
                        user_id TEXT NOT NULL,
                        title TEXT,
                        created_at TEXT NOT NULL,
                        updated_at TEXT NOT NULL,
                        metadata TEXT
                    );

                    CREATE INDEX IF NOT EXISTS idx_conv_tenant
                        ON conversations(tenant_id, updated_at DESC);

                    CREATE INDEX IF NOT EXISTS idx_conv_user
                        ON conversations(tenant_id, user_id, updated_at DESC);

                    CREATE TABLE IF NOT EXISTS messages (
                        id TEXT PRIMARY KEY,
                        conversation_id TEXT NOT NULL,
                        role TEXT NOT NULL,
                        content TEXT NOT NULL,
                        timestamp TEXT NOT NULL,
                        metadata TEXT,
                        FOREIGN KEY (conversation_id) REFERENCES conversations(id)
                    );

                    CREATE INDEX IF NOT EXISTS idx_msg_conv
                        ON messages(conversation_id, timestamp ASC);

                    CREATE TABLE IF NOT EXISTS feedbacks (
                        request_id TEXT PRIMARY KEY,
                        rating INTEGER NOT NULL,
                        comment TEXT,
                        created_at TEXT NOT NULL
                    );
                    """
                )
                conn.commit()
                self._initialized = True
            finally:
                conn.close()

    def _ensure_initialized_sqlserver(self) -> None:
        if self._initialized:
            return

        with self._lock:
            if self._initialized:
                return

            conn = self._get_sqlserver_connection()
            try:
                cursor = conn.cursor()
                cursor.execute(
                    """
                    IF OBJECT_ID('chat_conversations', 'U') IS NULL
                    BEGIN
                        CREATE TABLE chat_conversations (
                            id NVARCHAR(64) NOT NULL PRIMARY KEY,
                            tenant_id NVARCHAR(64) NOT NULL,
                            user_id NVARCHAR(128) NOT NULL,
                            title NVARCHAR(255) NULL,
                            metadata NVARCHAR(MAX) NULL,
                            created_at DATETIME2 NOT NULL,
                            updated_at DATETIME2 NOT NULL
                        )
                    END
                    """
                )
                cursor.execute(
                    """
                    IF NOT EXISTS (SELECT 1 FROM sys.indexes WHERE name = 'idx_chat_conv_tenant_updated' AND object_id = OBJECT_ID('chat_conversations'))
                    CREATE INDEX idx_chat_conv_tenant_updated ON chat_conversations(tenant_id, updated_at DESC)
                    """
                )
                cursor.execute(
                    """
                    IF NOT EXISTS (SELECT 1 FROM sys.indexes WHERE name = 'idx_chat_conv_tenant_user_updated' AND object_id = OBJECT_ID('chat_conversations'))
                    CREATE INDEX idx_chat_conv_tenant_user_updated ON chat_conversations(tenant_id, user_id, updated_at DESC)
                    """
                )
                cursor.execute(
                    """
                    IF OBJECT_ID('chat_messages', 'U') IS NULL
                    BEGIN
                        CREATE TABLE chat_messages (
                            id NVARCHAR(64) NOT NULL PRIMARY KEY,
                            conversation_id NVARCHAR(64) NOT NULL,
                            role NVARCHAR(16) NOT NULL,
                            content NVARCHAR(MAX) NOT NULL,
                            [timestamp] DATETIME2 NOT NULL,
                            metadata NVARCHAR(MAX) NULL
                        )
                    END
                    """
                )
                cursor.execute(
                    """
                    IF NOT EXISTS (SELECT 1 FROM sys.indexes WHERE name = 'idx_chat_messages_conv_ts' AND object_id = OBJECT_ID('chat_messages'))
                    CREATE INDEX idx_chat_messages_conv_ts ON chat_messages(conversation_id, [timestamp] ASC)
                    """
                )
                cursor.execute(
                    """
                    IF OBJECT_ID('chat_feedbacks', 'U') IS NULL
                    BEGIN
                        CREATE TABLE chat_feedbacks (
                            request_id NVARCHAR(128) NOT NULL PRIMARY KEY,
                            rating INT NOT NULL,
                            comment NVARCHAR(MAX) NULL,
                            created_at DATETIME2 NOT NULL
                        )
                    END
                    """
                )
                conn.commit()
                self._initialized = True
            finally:
                conn.close()

    @staticmethod
    def _safe_json_loads(payload: Any, fallback: Any) -> Any:
        try:
            return json.loads(payload) if payload not in (None, "") else fallback
        except (TypeError, json.JSONDecodeError):
            return fallback

    @staticmethod
    def _serialize_json(payload: Any, fallback: str) -> str:
        try:
            return json.dumps(payload, ensure_ascii=False, default=str)
        except (TypeError, ValueError):
            return fallback

    @staticmethod
    def _coerce_timestamp(raw_value: Any, fallback: datetime) -> str:
        if isinstance(raw_value, str):
            try:
                return datetime.fromisoformat(raw_value).isoformat()
            except ValueError:
                pass
        if isinstance(raw_value, (int, float)):
            try:
                return datetime.fromtimestamp(float(raw_value)).isoformat()
            except (OSError, OverflowError, ValueError):
                pass
        return fallback.isoformat()

    @staticmethod
    def _message_dict_from_row(row: sqlite3.Row) -> Dict[str, Any]:
        metadata = SessionManager._safe_json_loads(row["metadata"], None)
        item: Dict[str, Any] = {
            "id": row["id"],
            "role": row["role"],
            "content": row["content"],
            "timestamp": row["timestamp"],
        }
        if isinstance(metadata, dict) and metadata:
            item["metadata"] = metadata
        return item

    @staticmethod
    def _build_conversation_title(history: List[Dict[str, Any]]) -> Optional[str]:
        for message in history:
            if str(message.get("role", "")).lower() != "user":
                continue
            content = str(message.get("content", "")).strip()
            if content:
                single_line = " ".join(content.split())
                return single_line[:120]
        return None

    def _migrate_legacy_session_locked(self, conn: sqlite3.Connection, session_id: str, user_id: str) -> bool:
        if self._is_sqlserver_backend():
            return self._migrate_legacy_session_sqlserver_locked(conn, session_id, user_id)

        existing = conn.execute(
            "SELECT id, user_id FROM conversations WHERE id = ?",
            (session_id,),
        ).fetchone()
        if existing:
            return str(existing["user_id"]) == str(user_id)

        file_path = self._get_file_path(session_id)
        if not file_path.exists():
            return False

        try:
            with open(file_path, "r", encoding="utf-8") as handle:
                data = json.load(handle)
        except Exception as exc:
            logger.error("Error reading legacy session %s: %s", session_id, exc)
            return False

        owner_id = str(data.get("user_id") or user_id)
        if owner_id != str(user_id):
            logger.warning(
                "IDOR Attempt: User %s tried to migrate session %s owned by %s",
                user_id,
                session_id,
                owner_id,
            )
            return False

        history = data.get("history", [])
        if not isinstance(history, list):
            history = []

        created_at = datetime.utcnow()
        conversation_metadata = {
            "source": "legacy_json_import",
            "legacy_file": str(file_path),
        }

        conn.execute(
            """
            INSERT INTO conversations (id, tenant_id, user_id, title, created_at, updated_at, metadata)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                session_id,
                self.tenant_id,
                owner_id,
                self._build_conversation_title(history),
                created_at.isoformat(),
                created_at.isoformat(),
                self._serialize_json(conversation_metadata, "{}"),
            ),
        )

        for index, message in enumerate(history):
            if not isinstance(message, dict):
                continue

            message_time = created_at + timedelta(milliseconds=index)
            metadata = message.get("metadata") if isinstance(message.get("metadata"), dict) else None
            conn.execute(
                """
                INSERT INTO messages (id, conversation_id, role, content, timestamp, metadata)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    str(message.get("id") or f"msg-{uuid.uuid4().hex[:12]}"),
                    session_id,
                    str(message.get("role") or "user"),
                    str(message.get("content") or ""),
                    self._coerce_timestamp(message.get("timestamp"), message_time),
                    self._serialize_json(metadata, "null") if metadata is not None else None,
                ),
            )

        conn.commit()
        logger.info("Legacy session migrated to SQLite: session_id=%s", session_id)
        return True

    def _migrate_legacy_session_sqlserver_locked(self, conn, session_id: str, user_id: str) -> bool:
        cursor = conn.cursor()
        existing = self._sqlserver_execute(
            cursor,
            "SELECT id, user_id FROM chat_conversations WHERE id = ?",
            session_id,
        ).fetchone()
        if existing:
            return str(existing[1]) == str(user_id)

        file_path = self._get_file_path(session_id)
        if not file_path.exists():
            return False

        try:
            with open(file_path, "r", encoding="utf-8") as handle:
                data = json.load(handle)
        except Exception as exc:
            logger.error("Error reading legacy session %s: %s", session_id, exc)
            return False

        owner_id = str(data.get("user_id") or user_id)
        if owner_id != str(user_id):
            logger.warning(
                "IDOR Attempt: User %s tried to migrate session %s owned by %s",
                user_id,
                session_id,
                owner_id,
            )
            return False

        history = data.get("history", [])
        if not isinstance(history, list):
            history = []

        created_at = datetime.utcnow()
        self._sqlserver_execute(
            cursor,
            """
            INSERT INTO chat_conversations (id, tenant_id, user_id, title, created_at, updated_at, metadata)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            session_id,
            self.tenant_id,
            owner_id,
            self._build_conversation_title(history),
            created_at,
            created_at,
            self._serialize_json(
                {"source": "legacy_json_import", "legacy_file": str(file_path)},
                "{}",
            ),
        )

        for index, message in enumerate(history):
            if not isinstance(message, dict):
                continue
            message_time = created_at + timedelta(milliseconds=index)
            metadata = message.get("metadata") if isinstance(message.get("metadata"), dict) else None
            self._sqlserver_execute(
                cursor,
                """
                INSERT INTO chat_messages (id, conversation_id, role, content, [timestamp], metadata)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                str(message.get("id") or f"msg-{uuid.uuid4().hex[:12]}"),
                session_id,
                str(message.get("role") or "user"),
                str(message.get("content") or ""),
                datetime.fromisoformat(self._coerce_timestamp(message.get("timestamp"), message_time)),
                self._serialize_json(metadata, "null") if metadata is not None else None,
            )

        conn.commit()
        logger.info("Legacy session migrated to SQL Server: session_id=%s", session_id)
        return True

    def _ensure_conversation_locked(
        self,
        conn: sqlite3.Connection,
        session_id: str,
        user_id: str,
        content_hint: Optional[str] = None,
    ) -> bool:
        if self._is_sqlserver_backend():
            return self._ensure_conversation_sqlserver_locked(conn, session_id, user_id, content_hint)

        row = conn.execute(
            "SELECT id, user_id, title FROM conversations WHERE id = ?",
            (session_id,),
        ).fetchone()

        if row:
            if str(row["user_id"]) != str(user_id):
                logger.warning(
                    "IDOR Attempt: User %s tried to access session %s owned by %s",
                    user_id,
                    session_id,
                    row["user_id"],
                )
                return False
            return True

        if self._migrate_legacy_session_locked(conn, session_id, user_id):
            return True

        created_at = datetime.utcnow().isoformat()
        title = None
        if content_hint:
            title = " ".join(str(content_hint).split())[:120]

        conn.execute(
            """
            INSERT INTO conversations (id, tenant_id, user_id, title, created_at, updated_at, metadata)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                session_id,
                self.tenant_id,
                str(user_id),
                title,
                created_at,
                created_at,
                self._serialize_json({"session_id": session_id}, "{}"),
            ),
        )
        conn.commit()
        return True

    def _ensure_conversation_sqlserver_locked(
        self,
        conn,
        session_id: str,
        user_id: str,
        content_hint: Optional[str] = None,
    ) -> bool:
        row = self._sqlserver_execute(
            conn.cursor(),
            "SELECT id, user_id, title FROM chat_conversations WHERE id = ?",
            session_id,
        ).fetchone()

        if row:
            if str(row[1]) != str(user_id):
                logger.warning(
                    "IDOR Attempt: User %s tried to access session %s owned by %s",
                    user_id,
                    session_id,
                    row[1],
                )
                return False
            return True

        if self._migrate_legacy_session_sqlserver_locked(conn, session_id, user_id):
            return True

        created_at = datetime.utcnow()
        title = " ".join(str(content_hint).split())[:120] if content_hint else None
        cursor = conn.cursor()
        self._sqlserver_execute(
            cursor,
            """
            INSERT INTO chat_conversations (id, tenant_id, user_id, title, created_at, updated_at, metadata)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            session_id,
            self.tenant_id,
            str(user_id),
            title,
            created_at,
            created_at,
            self._serialize_json({"session_id": session_id}, "{}"),
        )
        conn.commit()
        return True

    def get_history(self, session_id: str, user_id: str) -> List[Dict[str, Any]]:
        """Retrieves recent chat history for a session, verified by user_id."""
        self._validate_session_id(session_id)
        self._ensure_initialized()

        if self._is_sqlserver_backend():
            return self._get_history_sqlserver(session_id, user_id)

        with self._lock:
            conn = self._get_connection()
            try:
                self._migrate_legacy_session_locked(conn, session_id, str(user_id))
                conversation = conn.execute(
                    "SELECT user_id FROM conversations WHERE id = ?",
                    (session_id,),
                ).fetchone()
                if not conversation:
                    return []
                if str(conversation["user_id"]) != str(user_id):
                    logger.warning(
                        "IDOR Attempt: User %s tried to access session %s owned by %s",
                        user_id,
                        session_id,
                        conversation["user_id"],
                    )
                    return []

                rows = conn.execute(
                    """
                    SELECT * FROM (
                        SELECT * FROM messages
                        WHERE conversation_id = ?
                        ORDER BY timestamp DESC
                        LIMIT ?
                    )
                    ORDER BY timestamp ASC
                    """,
                    (session_id, self.history_limit),
                ).fetchall()
                return [self._message_dict_from_row(row) for row in rows]
            except Exception as exc:
                logger.error("Error reading session %s: %s", session_id, exc)
                return []
            finally:
                conn.close()

    def _get_history_sqlserver(self, session_id: str, user_id: str) -> List[Dict[str, Any]]:
        with self._lock:
            conn = self._get_sqlserver_connection()
            try:
                self._migrate_legacy_session_sqlserver_locked(conn, session_id, str(user_id))
                cursor = conn.cursor()
                conversation = self._sqlserver_execute(
                    cursor,
                    "SELECT user_id FROM chat_conversations WHERE id = ?",
                    session_id,
                ).fetchone()
                if not conversation:
                    return []
                if str(conversation[0]) != str(user_id):
                    logger.warning(
                        "IDOR Attempt: User %s tried to access session %s owned by %s",
                        user_id,
                        session_id,
                        conversation[0],
                    )
                    return []

                rows = self._sqlserver_execute(
                    cursor,
                    """
                    SELECT TOP (?) id, role, content, [timestamp], metadata
                    FROM chat_messages
                    WHERE conversation_id = ?
                    ORDER BY [timestamp] DESC
                    """,
                    self.history_limit,
                    session_id,
                ).fetchall()
                ordered = list(reversed(rows))
                result: List[Dict[str, Any]] = []
                for row in ordered:
                    metadata = self._safe_json_loads(row[4], None)
                    item = {
                        "id": row[0],
                        "role": row[1],
                        "content": row[2],
                        "timestamp": row[3].isoformat() if hasattr(row[3], "isoformat") else str(row[3]),
                    }
                    if isinstance(metadata, dict) and metadata:
                        item["metadata"] = metadata
                    result.append(item)
                return result
            except Exception as exc:
                logger.error("Error reading SQL Server session %s: %s", session_id, exc)
                return []
            finally:
                conn.close()

    def get_full_history(self, session_id: str, user_id: str) -> List[Dict[str, Any]]:
        """Returns the full persisted history for a session."""
        self._validate_session_id(session_id)
        self._ensure_initialized()

        if self._is_sqlserver_backend():
            return self._get_full_history_sqlserver(session_id, user_id)

        with self._lock:
            conn = self._get_connection()
            try:
                self._migrate_legacy_session_locked(conn, session_id, str(user_id))
                conversation = conn.execute(
                    "SELECT user_id FROM conversations WHERE id = ?",
                    (session_id,),
                ).fetchone()
                if not conversation:
                    return []
                if str(conversation["user_id"]) != str(user_id):
                    logger.warning(
                        "IDOR Attempt: User %s tried to access session %s owned by %s",
                        user_id,
                        session_id,
                        conversation["user_id"],
                    )
                    return []

                rows = conn.execute(
                    """
                    SELECT * FROM messages
                    WHERE conversation_id = ?
                    ORDER BY timestamp ASC
                    """,
                    (session_id,),
                ).fetchall()
                return [self._message_dict_from_row(row) for row in rows]
            except Exception as exc:
                logger.error("Error reading full session %s: %s", session_id, exc)
                return []
            finally:
                conn.close()

    def _get_full_history_sqlserver(self, session_id: str, user_id: str) -> List[Dict[str, Any]]:
        with self._lock:
            conn = self._get_sqlserver_connection()
            try:
                self._migrate_legacy_session_sqlserver_locked(conn, session_id, str(user_id))
                cursor = conn.cursor()
                conversation = self._sqlserver_execute(
                    cursor,
                    "SELECT user_id FROM chat_conversations WHERE id = ?",
                    session_id,
                ).fetchone()
                if not conversation:
                    return []
                if str(conversation[0]) != str(user_id):
                    logger.warning(
                        "IDOR Attempt: User %s tried to access session %s owned by %s",
                        user_id,
                        session_id,
                        conversation[0],
                    )
                    return []

                rows = self._sqlserver_execute(
                    cursor,
                    """
                    SELECT id, role, content, [timestamp], metadata
                    FROM chat_messages
                    WHERE conversation_id = ?
                    ORDER BY [timestamp] ASC
                    """,
                    session_id,
                ).fetchall()
                result: List[Dict[str, Any]] = []
                for row in rows:
                    metadata = self._safe_json_loads(row[4], None)
                    item = {
                        "id": row[0],
                        "role": row[1],
                        "content": row[2],
                        "timestamp": row[3].isoformat() if hasattr(row[3], "isoformat") else str(row[3]),
                    }
                    if isinstance(metadata, dict) and metadata:
                        item["metadata"] = metadata
                    result.append(item)
                return result
            except Exception as exc:
                logger.error("Error reading full SQL Server session %s: %s", session_id, exc)
                return []
            finally:
                conn.close()

    def list_sessions(self, user_id: str, limit: int = 20, offset: int = 0) -> List[Dict[str, Any]]:
        """Lists persisted conversations for the current user."""
        self._ensure_initialized()

        if self._is_sqlserver_backend():
            return self._list_sessions_sqlserver(user_id, limit=limit, offset=offset)

        with self._lock:
            conn = self._get_connection()
            try:
                rows = conn.execute(
                    """
                    SELECT
                        c.id,
                        c.title,
                        c.created_at,
                        c.updated_at,
                        COUNT(m.id) AS message_count
                    FROM conversations c
                    LEFT JOIN messages m ON m.conversation_id = c.id
                    WHERE c.user_id = ?
                    GROUP BY c.id, c.title, c.created_at, c.updated_at
                    ORDER BY c.updated_at DESC
                    LIMIT ? OFFSET ?
                    """,
                    (str(user_id), max(1, int(limit)), max(0, int(offset))),
                ).fetchall()
                return [
                    {
                        "id": row["id"],
                        "title": row["title"],
                        "created_at": row["created_at"],
                        "updated_at": row["updated_at"],
                        "message_count": int(row["message_count"] or 0),
                    }
                    for row in rows
                ]
            except Exception as exc:
                logger.error("Error listing sessions for user %s: %s", user_id, exc)
                return []
            finally:
                conn.close()

    def _list_sessions_sqlserver(self, user_id: str, limit: int = 20, offset: int = 0) -> List[Dict[str, Any]]:
        with self._lock:
            conn = self._get_sqlserver_connection()
            try:
                cursor = conn.cursor()
                rows = self._sqlserver_execute(
                    cursor,
                    """
                    SELECT
                        c.id,
                        c.title,
                        c.created_at,
                        c.updated_at,
                        COUNT(m.id) AS message_count
                    FROM chat_conversations c
                    LEFT JOIN chat_messages m ON m.conversation_id = c.id
                    WHERE c.user_id = ?
                    GROUP BY c.id, c.title, c.created_at, c.updated_at
                    ORDER BY c.updated_at DESC
                    OFFSET ? ROWS FETCH NEXT ? ROWS ONLY
                    """,
                    str(user_id),
                    max(0, int(offset)),
                    max(1, int(limit)),
                ).fetchall()
                return [
                    {
                        "id": row[0],
                        "title": row[1],
                        "created_at": row[2].isoformat() if hasattr(row[2], "isoformat") else str(row[2]),
                        "updated_at": row[3].isoformat() if hasattr(row[3], "isoformat") else str(row[3]),
                        "message_count": int(row[4] or 0),
                    }
                    for row in rows
                ]
            except Exception as exc:
                logger.error("Error listing SQL Server sessions for user %s: %s", user_id, exc)
                return []
            finally:
                conn.close()

    def add_message(
        self,
        session_id: str,
        role: str,
        content: str,
        user_id: str,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Adds a message to the persisted session history."""
        self._validate_session_id(session_id)
        self._ensure_initialized()

        if self._is_sqlserver_backend():
            self._add_message_sqlserver(
                session_id=session_id,
                role=role,
                content=content,
                user_id=user_id,
                metadata=metadata,
            )
            return

        normalized_metadata = metadata if isinstance(metadata, dict) and metadata else None

        with self._lock:
            conn = self._get_connection()
            try:
                title_hint = content if str(role or "").lower() == "user" else None
                if not self._ensure_conversation_locked(conn, session_id, str(user_id), content_hint=title_hint):
                    return

                timestamp = datetime.utcnow().isoformat()
                conn.execute(
                    """
                    INSERT INTO messages (id, conversation_id, role, content, timestamp, metadata)
                    VALUES (?, ?, ?, ?, ?, ?)
                    """,
                    (
                        f"msg-{uuid.uuid4().hex[:12]}",
                        session_id,
                        str(role or "user"),
                        str(content or ""),
                        timestamp,
                        self._serialize_json(normalized_metadata, "null") if normalized_metadata is not None else None,
                    ),
                )

                conn.execute(
                    """
                    UPDATE conversations
                    SET updated_at = ?,
                        title = CASE
                            WHEN (title IS NULL OR title = '') AND ? IS NOT NULL AND ? != '' THEN ?
                            ELSE title
                        END
                    WHERE id = ?
                    """,
                    (
                        timestamp,
                        title_hint,
                        title_hint,
                        " ".join(str(title_hint).split())[:120] if title_hint else None,
                        session_id,
                    ),
                )
                conn.commit()
            except Exception as exc:
                logger.error("Error saving session %s: %s", session_id, exc)
            finally:
                conn.close()

    def _add_message_sqlserver(
        self,
        session_id: str,
        role: str,
        content: str,
        user_id: str,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> None:
        normalized_metadata = metadata if isinstance(metadata, dict) and metadata else None
        with self._lock:
            conn = self._get_sqlserver_connection()
            try:
                title_hint = content if str(role or "").lower() == "user" else None
                if not self._ensure_conversation_sqlserver_locked(conn, session_id, str(user_id), content_hint=title_hint):
                    return

                cursor = conn.cursor()
                timestamp = datetime.utcnow()
                self._sqlserver_execute(
                    cursor,
                    """
                    INSERT INTO chat_messages (id, conversation_id, role, content, [timestamp], metadata)
                    VALUES (?, ?, ?, ?, ?, ?)
                    """,
                    f"msg-{uuid.uuid4().hex[:12]}",
                    session_id,
                    str(role or "user"),
                    str(content or ""),
                    timestamp,
                    self._serialize_json(normalized_metadata, "null") if normalized_metadata is not None else None,
                )

                self._sqlserver_execute(
                    cursor,
                    """
                    UPDATE chat_conversations
                    SET updated_at = ?,
                        title = CASE
                            WHEN (title IS NULL OR title = '') AND ? IS NOT NULL AND ? <> '' THEN ?
                            ELSE title
                        END
                    WHERE id = ?
                    """,
                    timestamp,
                    title_hint,
                    title_hint,
                    " ".join(str(title_hint).split())[:120] if title_hint else None,
                    session_id,
                )
                conn.commit()
            except Exception as exc:
                logger.error("Error saving SQL Server session %s: %s", session_id, exc)
            finally:
                conn.close()

    def update_message_metadata_by_request_id(
        self,
        session_id: str,
        user_id: str,
        request_id: str,
        metadata_patch: Dict[str, Any],
    ) -> bool:
        """Updates the latest message metadata that matches a persisted request_id."""
        self._validate_session_id(session_id)
        self._ensure_initialized()

        if self._is_sqlserver_backend():
            return self._update_message_metadata_by_request_id_sqlserver(
                session_id=session_id,
                user_id=user_id,
                request_id=request_id,
                metadata_patch=metadata_patch,
            )

        normalized_request_id = str(request_id or "").strip()
        if not normalized_request_id or not isinstance(metadata_patch, dict) or not metadata_patch:
            return False

        with self._lock:
            conn = self._get_connection()
            try:
                if not self._ensure_conversation_locked(conn, session_id, str(user_id)):
                    return False

                rows = conn.execute(
                    """
                    SELECT id, metadata
                    FROM messages
                    WHERE conversation_id = ?
                    ORDER BY timestamp DESC
                    """,
                    (session_id,),
                ).fetchall()

                for row in rows:
                    existing_metadata = self._safe_json_loads(row["metadata"], None)
                    if not isinstance(existing_metadata, dict):
                        continue

                    existing_request_id = str(existing_metadata.get("request_id") or "").strip()
                    ui_payload = existing_metadata.get("ui_payload")
                    if not existing_request_id and isinstance(ui_payload, dict):
                        existing_request_id = str(ui_payload.get("request_id") or "").strip()
                    if existing_request_id != normalized_request_id:
                        continue

                    merged_metadata = dict(existing_metadata)
                    for key, value in metadata_patch.items():
                        if key == "ui_payload" and isinstance(value, dict):
                            existing_ui_payload = (
                                merged_metadata.get("ui_payload")
                                if isinstance(merged_metadata.get("ui_payload"), dict)
                                else {}
                            )
                            merged_metadata["ui_payload"] = {
                                **existing_ui_payload,
                                **value,
                            }
                            continue
                        merged_metadata[key] = value

                    conn.execute(
                        """
                        UPDATE messages
                        SET metadata = ?
                        WHERE id = ?
                        """,
                        (
                            self._serialize_json(merged_metadata, "null"),
                            row["id"],
                        ),
                    )
                    conn.execute(
                        """
                        UPDATE conversations
                        SET updated_at = ?
                        WHERE id = ?
                        """,
                        (datetime.utcnow().isoformat(), session_id),
                    )
                    conn.commit()
                    return True
                return False
            except Exception as exc:
                logger.error(
                    "Error updating metadata for session %s request %s: %s",
                    session_id,
                    normalized_request_id,
                    exc,
                )
                return False
            finally:
                conn.close()

    def _update_message_metadata_by_request_id_sqlserver(
        self,
        session_id: str,
        user_id: str,
        request_id: str,
        metadata_patch: Dict[str, Any],
    ) -> bool:
        normalized_request_id = str(request_id or "").strip()
        if not normalized_request_id or not isinstance(metadata_patch, dict) or not metadata_patch:
            return False

        with self._lock:
            conn = self._get_sqlserver_connection()
            try:
                if not self._ensure_conversation_sqlserver_locked(conn, session_id, str(user_id)):
                    return False

                cursor = conn.cursor()
                rows = self._sqlserver_execute(
                    cursor,
                    """
                    SELECT id, metadata
                    FROM chat_messages
                    WHERE conversation_id = ?
                    ORDER BY [timestamp] DESC
                    """,
                    session_id,
                ).fetchall()

                for row in rows:
                    existing_metadata = self._safe_json_loads(row[1], None)
                    if not isinstance(existing_metadata, dict):
                        continue

                    existing_request_id = str(existing_metadata.get("request_id") or "").strip()
                    ui_payload = existing_metadata.get("ui_payload")
                    if not existing_request_id and isinstance(ui_payload, dict):
                        existing_request_id = str(ui_payload.get("request_id") or "").strip()
                    if existing_request_id != normalized_request_id:
                        continue

                    merged_metadata = dict(existing_metadata)
                    for key, value in metadata_patch.items():
                        if key == "ui_payload" and isinstance(value, dict):
                            existing_ui_payload = (
                                merged_metadata.get("ui_payload")
                                if isinstance(merged_metadata.get("ui_payload"), dict)
                                else {}
                            )
                            merged_metadata["ui_payload"] = {
                                **existing_ui_payload,
                                **value,
                            }
                            continue
                        merged_metadata[key] = value

                    self._sqlserver_execute(
                        cursor,
                        """
                        UPDATE chat_messages
                        SET metadata = ?
                        WHERE id = ?
                        """,
                        self._serialize_json(merged_metadata, "null"),
                        row[0],
                    )
                    self._sqlserver_execute(
                        cursor,
                        """
                        UPDATE chat_conversations
                        SET updated_at = ?
                        WHERE id = ?
                        """,
                        datetime.utcnow(),
                        session_id,
                    )
                    conn.commit()
                    return True
                return False
            except Exception as exc:
                logger.error(
                    "Error updating SQL Server metadata for session %s request %s: %s",
                    session_id,
                    normalized_request_id,
                    exc,
                )
                return False
            finally:
                conn.close()

    def clear_session(self, session_id: str, user_id: Optional[str] = None) -> None:
        """Deletes a persisted session and any legacy backup file."""
        self._validate_session_id(session_id)
        self._ensure_initialized()

        if self._is_sqlserver_backend():
            self._clear_session_sqlserver(session_id, user_id=user_id)
            return

        with self._lock:
            conn = self._get_connection()
            try:
                if user_id:
                    row = conn.execute(
                        "SELECT user_id FROM conversations WHERE id = ?",
                        (session_id,),
                    ).fetchone()
                    if row and str(row["user_id"]) != str(user_id):
                        logger.warning(
                            "IDOR Attempt: User %s tried to clear session %s owned by %s",
                            user_id,
                            session_id,
                            row["user_id"],
                        )
                        return

                conn.execute("DELETE FROM messages WHERE conversation_id = ?", (session_id,))
                conn.execute("DELETE FROM conversations WHERE id = ?", (session_id,))
                conn.commit()
            except Exception as exc:
                logger.error("Error clearing session %s: %s", session_id, exc)
            finally:
                conn.close()

        file_path = self._get_file_path(session_id)
        if file_path.exists():
            try:
                os.remove(file_path)
            except Exception as exc:
                logger.error("Error clearing legacy session file %s: %s", session_id, exc)

    def _clear_session_sqlserver(self, session_id: str, user_id: Optional[str] = None) -> None:
        with self._lock:
            conn = self._get_sqlserver_connection()
            try:
                cursor = conn.cursor()
                if user_id:
                    row = self._sqlserver_execute(
                        cursor,
                        "SELECT user_id FROM chat_conversations WHERE id = ?",
                        session_id,
                    ).fetchone()
                    if row and str(row[0]) != str(user_id):
                        logger.warning(
                            "IDOR Attempt: User %s tried to clear session %s owned by %s",
                            user_id,
                            session_id,
                            row[0],
                        )
                        return

                self._sqlserver_execute(cursor, "DELETE FROM chat_messages WHERE conversation_id = ?", session_id)
                self._sqlserver_execute(cursor, "DELETE FROM chat_conversations WHERE id = ?", session_id)
                conn.commit()
            except Exception as exc:
                logger.error("Error clearing SQL Server session %s: %s", session_id, exc)
            finally:
                conn.close()

        file_path = self._get_file_path(session_id)
        if file_path.exists():
            try:
                os.remove(file_path)
            except Exception as exc:
                logger.error("Error clearing legacy session file %s: %s", session_id, exc)

    def delete_session(self, session_id: str, user_id: Optional[str] = None) -> None:
        """Backward-compatible alias for deleting a session."""
        self.clear_session(session_id, user_id=user_id)
