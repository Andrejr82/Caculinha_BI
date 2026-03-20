import uuid
from unittest.mock import AsyncMock, Mock

import pytest

from backend.app.core.utils.session_manager import SessionManager
from backend.app.services.chat_service_v3 import ChatServiceV3
from backend.domain.entities.memory_entry import MemoryEntry


@pytest.mark.asyncio
async def test_retrieve_cross_session_memory_filters_current_session_and_user():
    session_manager = Mock(spec=SessionManager)
    session_manager.list_sessions.return_value = []
    service = ChatServiceV3(session_manager=session_manager)
    service._hydrate_user_memory_index = AsyncMock()
    service.memory_rag_agent = Mock()
    service.memory_rag_agent.search = AsyncMock(
        return_value=[
            MemoryEntry(
                conversation_id="sess-old",
                content="Histórico relevante de uma sessão anterior.",
                metadata={"user_id": "user-1"},
            ),
            MemoryEntry(
                conversation_id="sess-current",
                content="Mensagem da sessão atual que não deve entrar.",
                metadata={"user_id": "user-1"},
            ),
            MemoryEntry(
                conversation_id="sess-other-user",
                content="Contexto de outro usuário que deve ser descartado.",
                metadata={"user_id": "user-2"},
            ),
        ]
    )

    results = await service._retrieve_cross_session_memory(
        query="retome a análise",
        session_id="sess-current",
        user_id="user-1",
    )

    assert len(results) == 1
    assert results[0].conversation_id == "sess-old"
    assert "sess-current" not in [entry.conversation_id for entry in results]


@pytest.mark.asyncio
async def test_process_message_prepends_retrieved_memory_to_agent_history():
    session_manager = Mock(spec=SessionManager)
    session_manager.get_history.return_value = [
        {"role": "user", "content": "Mostre a margem do item 123"},
    ]
    session_manager.list_sessions.return_value = []
    service = ChatServiceV3(session_manager=session_manager)
    service._retrieve_cross_session_memory = AsyncMock(
        return_value=[
            MemoryEntry(
                conversation_id="sess-prev",
                content="Na sessão anterior o usuário pediu foco em margem por loja.",
                metadata={"user_id": "user-1", "response_type": "table"},
            )
        ]
    )
    service._index_memory_message = AsyncMock()

    agent = Mock()
    agent.run_async = AsyncMock(return_value={"response": "Resposta final com contexto."})
    service._agents_by_role["analyst"] = agent

    response = await service.process_message(
        query="E agora, qual loja piorou?",
        session_id="sess-current",
        user_id="user-1",
        user_role="analyst",
    )

    called_history = agent.run_async.await_args.args[1]

    assert "Resposta final com contexto." in response["result"]["mensagem"]
    assert called_history[0]["role"] == "system"
    assert "Contexto relevante recuperado" in called_history[0]["content"]
    assert "margem por loja" in called_history[0]["content"]
    assert called_history[1]["content"] == "Mostre a margem do item 123"
    assert service._index_memory_message.await_count == 2


@pytest.mark.asyncio
async def test_process_message_recovers_context_from_previous_persisted_session(tmp_path, monkeypatch):
    db_path = tmp_path / "agentbi.db"
    monkeypatch.setattr(
        SessionManager,
        "default_db_path",
        staticmethod(lambda: db_path),
    )

    session_manager = SessionManager(
        storage_dir=str(tmp_path / "sessions"),
        db_path=str(db_path),
    )
    previous_session_id = str(uuid.uuid4())
    current_session_id = str(uuid.uuid4())
    user_id = "user-1"

    session_manager.add_message(
        previous_session_id,
        "user",
        "Quero foco em margem por loja do item 123",
        user_id,
        metadata={"request_id": "prev-user"},
    )
    session_manager.add_message(
        previous_session_id,
        "assistant",
        "Na sessão anterior o foco foi margem por loja do item 123.",
        user_id,
        metadata={"request_id": "prev-assistant", "source": "tool.consultar_dados_flexivel"},
    )

    service = ChatServiceV3(session_manager=session_manager)
    agent = Mock()
    agent.run_async = AsyncMock(return_value={"response": "Resposta atual com apoio de memória."})
    service._agents_by_role["analyst"] = agent

    response = await service.process_message(
        query="E agora, quais lojas pioraram?",
        session_id=current_session_id,
        user_id=user_id,
        user_role="analyst",
    )

    called_history = agent.run_async.await_args.args[1]

    assert "Resposta atual com apoio de memória." in response["result"]["mensagem"]
    assert called_history[0]["role"] == "system"
    assert "margem por loja do item 123" in called_history[0]["content"]


@pytest.mark.asyncio
async def test_process_message_prepends_user_preferences_to_agent_history():
    session_manager = Mock(spec=SessionManager)
    session_manager.get_history.return_value = []
    session_manager.list_sessions.return_value = []
    service = ChatServiceV3(session_manager=session_manager)
    service._load_user_preferences = AsyncMock(
        return_value={
            "language": "pt-BR",
            "preferred_data_format": "table",
            "preferred_chart_type": "line",
            "analysis_focus": "inventory",
            "company_name": "Caçulinha BI",
        }
    )
    service._retrieve_cross_session_memory = AsyncMock(return_value=[])
    service._index_memory_message = AsyncMock()

    agent = Mock()
    agent.run_async = AsyncMock(return_value={"response": "Resposta alinhada às preferências."})
    service._agents_by_role["analyst"] = agent

    response = await service.process_message(
        query="Mostre o panorama atual",
        session_id="sess-current",
        user_id="12345678-1234-1234-1234-123456789012",
        user_role="analyst",
    )

    called_history = agent.run_async.await_args.args[1]

    assert "Resposta alinhada às preferências." in response["result"]["mensagem"]
    assert called_history[0]["role"] == "system"
    assert "Responda preferencialmente em pt-BR" in called_history[0]["content"]
    assert "Prefira respostas tabulares" in called_history[0]["content"]
    assert "tipo line" in called_history[0]["content"]
    assert "Caçulinha BI" in called_history[0]["content"]


@pytest.mark.asyncio
async def test_process_message_skips_memory_retrieval_and_persistence_when_memory_capability_disabled():
    session_manager = Mock(spec=SessionManager)
    service = ChatServiceV3(session_manager=session_manager)
    service._load_user_preferences = AsyncMock(return_value={"preferred_data_format": "table"})
    service._retrieve_cross_session_memory = AsyncMock(return_value=[])
    service._index_memory_message = AsyncMock()

    agent = Mock()
    agent.run_async = AsyncMock(return_value={"response": "Resposta sem memória persistente."})
    service._agents_by_role["analyst"] = agent

    response = await service.process_message(
        query="Retome a análise atual",
        session_id="sess-no-memory",
        user_id="user-1",
        user_role="analyst",
        user_capabilities={"memory": False, "multimodal": True, "computer_use": False},
    )

    called_history = agent.run_async.await_args.args[1]

    assert "Resposta sem memória persistente." in response["result"]["mensagem"]
    assert called_history == []
    session_manager.get_history.assert_not_called()
    service._load_user_preferences.assert_not_awaited()
    service._retrieve_cross_session_memory.assert_not_awaited()
    session_manager.add_message.assert_not_called()
    service._index_memory_message.assert_not_awaited()


@pytest.mark.asyncio
async def test_process_message_blocks_image_generation_when_multimodal_capability_disabled():
    session_manager = Mock(spec=SessionManager)
    session_manager.get_history.return_value = []
    session_manager.list_sessions.return_value = []
    service = ChatServiceV3(session_manager=session_manager)
    service._load_user_preferences = AsyncMock(return_value={})
    service._retrieve_cross_session_memory = AsyncMock(return_value=[])
    service.image_generation_service = Mock()
    service.image_generation_service.generate_image = AsyncMock()

    agent = Mock()
    agent.run_async = AsyncMock(return_value={"response": "Não deveria executar."})
    service._agents_by_role["analyst"] = agent

    response = await service.process_message(
        query="Gere uma imagem do dashboard executivo",
        session_id="sess-image-block",
        user_id="user-1",
        user_role="analyst",
        user_capabilities={"memory": True, "multimodal": False, "computer_use": False},
    )

    assert response["mode"] == "policy_block"
    assert response["source"] == "policy.capability.multimodal"
    assert "não estão habilitados" in response["result"]["mensagem"]
    agent.run_async.assert_not_called()
    service.image_generation_service.generate_image.assert_not_awaited()
