import json
import uuid
from pathlib import Path

from backend.app.core.utils.session_manager import SessionManager


def test_session_manager_persists_messages_across_instances(tmp_path: Path):
    storage_dir = tmp_path / "sessions"
    db_path = tmp_path / "agentbi.db"
    session_id = str(uuid.uuid4())
    user_id = "user-123"

    manager = SessionManager(storage_dir=str(storage_dir), db_path=str(db_path))
    manager.add_message(
        session_id,
        "user",
        "Quero analisar margem por loja",
        user_id,
        metadata={"request_id": "req-user-1"},
    )
    manager.add_message(
        session_id,
        "assistant",
        "Segue a análise consolidada.",
        user_id,
        metadata={
            "request_id": "req-assistant-1",
            "source": "tool.consultar_dados_flexivel",
            "ui_payload": {
                "type": "table",
                "data": [{"une": "1685", "margem": 12.4}],
                "request_id": "req-assistant-1",
            },
        },
    )

    reloaded = SessionManager(storage_dir=str(storage_dir), db_path=str(db_path))
    history = reloaded.get_full_history(session_id, user_id)
    sessions = reloaded.list_sessions(user_id)

    assert [item["role"] for item in history] == ["user", "assistant"]
    assert history[1]["metadata"]["request_id"] == "req-assistant-1"
    assert history[1]["metadata"]["ui_payload"]["data"][0]["une"] == "1685"
    assert sessions[0]["id"] == session_id
    assert sessions[0]["message_count"] == 2


def test_session_manager_migrates_legacy_json_history(tmp_path: Path):
    storage_dir = tmp_path / "sessions"
    storage_dir.mkdir(parents=True, exist_ok=True)
    db_path = tmp_path / "agentbi.db"
    session_id = str(uuid.uuid4())
    user_id = "legacy-user"

    legacy_payload = {
        "user_id": user_id,
        "history": [
            {"role": "user", "content": "Mostre a ruptura por loja"},
            {
                "role": "assistant",
                "content": "Encontrei os principais pontos de ruptura.",
                "metadata": {"request_id": "legacy-response-1"},
            },
        ],
    }
    (storage_dir / f"{session_id}.json").write_text(
        json.dumps(legacy_payload, ensure_ascii=False),
        encoding="utf-8",
    )

    manager = SessionManager(storage_dir=str(storage_dir), db_path=str(db_path))
    history = manager.get_full_history(session_id, user_id)
    sessions = manager.list_sessions(user_id)

    assert len(history) == 2
    assert history[0]["content"] == "Mostre a ruptura por loja"
    assert history[1]["metadata"]["request_id"] == "legacy-response-1"
    assert sessions[0]["title"] == "Mostre a ruptura por loja"


def test_session_manager_enforces_user_ownership(tmp_path: Path):
    storage_dir = tmp_path / "sessions"
    db_path = tmp_path / "agentbi.db"
    session_id = str(uuid.uuid4())

    manager = SessionManager(storage_dir=str(storage_dir), db_path=str(db_path))
    manager.add_message(session_id, "user", "Mensagem privada", "owner-user")
    manager.add_message(session_id, "assistant", "Resposta privada", "owner-user")
    manager.add_message(session_id, "assistant", "Tentativa indevida", "intruder-user")

    owner_history = manager.get_full_history(session_id, "owner-user")
    intruder_history = manager.get_full_history(session_id, "intruder-user")

    assert len(owner_history) == 2
    assert owner_history[-1]["content"] == "Resposta privada"
    assert intruder_history == []
