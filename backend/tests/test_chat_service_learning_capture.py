from unittest.mock import AsyncMock, Mock, patch

import pytest

from backend.app.core.utils.session_manager import SessionManager
from backend.app.services.chat_service_v3 import ChatServiceV3


@pytest.mark.asyncio
async def test_process_message_captures_high_quality_example_and_rebuilds_dataset():
    session_manager = Mock(spec=SessionManager)
    session_manager.get_history.return_value = []
    session_manager.list_sessions.return_value = []

    service = ChatServiceV3(session_manager=session_manager)
    service._load_user_preferences = AsyncMock(return_value={})
    service._retrieve_cross_session_memory = AsyncMock(return_value=[])
    service._retrieve_document_context = AsyncMock(return_value=[])
    service._index_memory_message = AsyncMock()
    service.example_collector = Mock()
    service.example_collector.add_example.return_value = True

    agent = Mock()
    agent.run_async = AsyncMock(
        return_value={
            "response": "Análise concluída com visualização gerada.",
            "chart_data": {"type": "bar", "labels": ["1685"], "datasets": [{"data": [311492.84]}]},
            "source": "tool.consultar_dados_flexivel",
            "confidence": 0.91,
            "tool_calls": [{"function": {"name": "consultar_dados_flexivel"}}],
        }
    )
    service._agents_by_role["analyst"] = agent

    with patch("backend.app.services.chat_service_v3.build_default_unified_learning_dataset") as mock_rebuild:
        response = await service.process_message(
            query="quero um gráfico de vendas do segmento tecidos por loja",
            session_id="sess-1",
            user_id="user-1",
            user_role="analyst",
        )

    assert "Análise concluída" in response["result"]["mensagem"]
    service.example_collector.add_example.assert_called_once()
    payload = service.example_collector.add_example.call_args.kwargs
    assert payload["query"] == "quero um gráfico de vendas do segmento tecidos por loja"
    assert payload["intent"] == "visualization"
    mock_rebuild.assert_called_once()


@pytest.mark.asyncio
async def test_process_message_skips_capture_for_degraded_response():
    session_manager = Mock(spec=SessionManager)
    session_manager.get_history.return_value = []
    session_manager.list_sessions.return_value = []

    service = ChatServiceV3(session_manager=session_manager)
    service._load_user_preferences = AsyncMock(return_value={})
    service._retrieve_cross_session_memory = AsyncMock(return_value=[])
    service._retrieve_document_context = AsyncMock(return_value=[])
    service._index_memory_message = AsyncMock()
    service.example_collector = Mock()
    service.example_collector.add_example.return_value = True

    agent = Mock()
    agent.run_async = AsyncMock(
        return_value={
            "response": "Não consegui gerar o gráfico: Não encontrei dados para montar o gráfico nesse recorte.",
            "source": "tool.gerar_grafico_universal_v2",
            "confidence": 0.18,
            "tool_calls": [{"function": {"name": "gerar_grafico_universal_v2"}}],
        }
    )
    service._agents_by_role["analyst"] = agent

    with patch("backend.app.services.chat_service_v3.build_default_unified_learning_dataset") as mock_rebuild:
        response = await service.process_message(
            query="me de o gráfico do segmento festas de cada loja",
            session_id="sess-2",
            user_id="user-1",
            user_role="analyst",
        )

    assert "Não consegui gerar o gráfico" in response["result"]["mensagem"]
    service.example_collector.add_example.assert_not_called()
    mock_rebuild.assert_not_called()
