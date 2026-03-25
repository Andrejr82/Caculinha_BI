import json
import logging
import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional

from backend.app.config.settings import settings
from backend.app.core.learning.chat_example_capture import build_chat_example_payload
from backend.app.core.learning.unified_dataset_builder import build_default_unified_learning_dataset
from backend.app.core.rag.example_collector import ExampleCollector
from backend.app.core.utils.session_manager import SessionManager

logger = logging.getLogger(__name__)


def _safe_json_loads(payload: Any) -> Dict[str, Any]:
    if payload in (None, ""):
        return {}
    try:
        loaded = json.loads(payload)
    except (TypeError, json.JSONDecodeError):
        return {}
    return loaded if isinstance(loaded, dict) else {}


def _parse_timestamp(raw_value: Any) -> Optional[datetime]:
    if not isinstance(raw_value, str) or not raw_value.strip():
        return None
    try:
        return datetime.fromisoformat(raw_value)
    except ValueError:
        return None


def backfill_examples_from_session_db(
    *,
    db_path: Optional[str] = None,
    examples_dir: Optional[str] = None,
    rebuild_dataset: bool = True,
) -> Dict[str, int]:
    resolved_db_path = Path(db_path or SessionManager.default_db_path())
    collector = ExampleCollector(examples_dir=examples_dir or settings.LEARNING_EXAMPLES_PATH)

    if not resolved_db_path.exists():
        return {"scanned": 0, "captured": 0, "skipped": 0, "duplicates": 0}

    scanned = 0
    captured = 0
    skipped = 0
    duplicates = 0
    last_user_by_conversation: Dict[str, Dict[str, Any]] = {}

    conn = sqlite3.connect(resolved_db_path)
    conn.row_factory = sqlite3.Row
    try:
        rows = conn.execute(
            """
            SELECT
                c.user_id AS conversation_user_id,
                m.conversation_id,
                m.role,
                m.content,
                m.timestamp,
                m.metadata
            FROM messages m
            JOIN conversations c ON c.id = m.conversation_id
            ORDER BY m.conversation_id ASC, m.timestamp ASC
            """
        ).fetchall()
    finally:
        conn.close()

    for row in rows:
        role = str(row["role"] or "").strip().lower()
        conversation_id = str(row["conversation_id"] or "")
        content = str(row["content"] or "")
        metadata = _safe_json_loads(row["metadata"])

        if role == "user":
            last_user_by_conversation[conversation_id] = {
                "content": content,
                "timestamp": row["timestamp"],
                "metadata": metadata,
            }
            continue

        if role != "assistant":
            continue

        scanned += 1
        paired_user = last_user_by_conversation.get(conversation_id)
        if not paired_user:
            skipped += 1
            continue

        payload = build_chat_example_payload(
            query=paired_user["content"],
            user_id=str(row["conversation_user_id"] or "anonymous"),
            assistant_text=content,
            assistant_metadata=metadata,
            timestamp=_parse_timestamp(row["timestamp"]),
        )
        if payload is None:
            skipped += 1
            continue

        inserted = collector.add_example(**payload)
        if inserted:
            captured += 1
        else:
            duplicates += 1

    if rebuild_dataset and captured > 0:
        try:
            build_default_unified_learning_dataset()
        except Exception as exc:
            logger.warning("Falha ao reconstruir dataset unificado durante backfill: %s", exc, exc_info=True)

    return {
        "scanned": scanned,
        "captured": captured,
        "skipped": skipped,
        "duplicates": duplicates,
    }
