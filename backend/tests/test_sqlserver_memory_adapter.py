from pathlib import Path

import pytest
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from backend.domain.entities.conversation import Conversation
from backend.domain.entities.message import Message
from backend.infrastructure.adapters.sqlserver_memory_adapter import SQLServerMemoryAdapter


@pytest.mark.asyncio
async def test_sqlserver_memory_adapter_crud_roundtrip(tmp_path: Path):
    db_path = tmp_path / "chat_state.db"
    engine = create_async_engine(f"sqlite+aiosqlite:///{db_path}")
    session_factory = async_sessionmaker(engine, expire_on_commit=False)
    adapter = SQLServerMemoryAdapter(session_factory=session_factory, engine=engine)

    conversation = Conversation(tenant_id="default", user_id="user-1", title="Teste SQL")
    await adapter.save_conversation(conversation)
    await adapter.add_message(Message.user(conversation.id, "Pergunta inicial"))
    await adapter.add_message(Message.assistant(conversation.id, "Resposta inicial"))

    loaded = await adapter.get_conversation(conversation.id)
    all_messages = await adapter.get_all_messages(conversation.id)
    recent_messages = await adapter.get_recent_messages(conversation.id, limit=1)
    listed = await adapter.list_conversations(tenant_id="default", user_id="user-1")

    assert loaded is not None
    assert loaded.title == "Teste SQL"
    assert len(all_messages) == 2
    assert all_messages[0].role == "user"
    assert recent_messages[0].role == "assistant"
    assert listed[0].id == conversation.id
    assert await adapter.count_messages(conversation.id) == 2

    await engine.dispose()


@pytest.mark.asyncio
async def test_sqlserver_memory_adapter_saves_feedback_and_delete_conversation(tmp_path: Path):
    db_path = tmp_path / "chat_state.db"
    engine = create_async_engine(f"sqlite+aiosqlite:///{db_path}")
    session_factory = async_sessionmaker(engine, expire_on_commit=False)
    adapter = SQLServerMemoryAdapter(session_factory=session_factory, engine=engine)

    conversation = Conversation(tenant_id="default", user_id="user-2", title="Feedback SQL")
    await adapter.save_conversation(conversation)
    message = Message.user(conversation.id, "Mensagem")
    await adapter.add_message(message)
    await adapter.save_feedback("req-1", 5, "ok")

    assert await adapter.get_message(message.id) is not None
    assert await adapter.delete_message(message.id) is True
    assert await adapter.count_messages(conversation.id) == 0
    assert await adapter.delete_conversation(conversation.id) is True
    assert await adapter.get_conversation(conversation.id) is None

    await engine.dispose()
