from unittest.mock import AsyncMock, Mock

import pytest

from backend.app.core.utils.session_manager import SessionManager
from backend.app.services.chat_service_v3 import ChatServiceV3


@pytest.mark.asyncio
async def test_process_message_uses_internal_document_context_and_emits_citations():
    session_manager = Mock(spec=SessionManager)
    session_manager.get_history.return_value = []
    session_manager.list_sessions.return_value = []

    service = ChatServiceV3(session_manager=session_manager)
    service._load_user_preferences = AsyncMock(return_value={})
    service._retrieve_cross_session_memory = AsyncMock(return_value=[])
    service._retrieve_document_context = AsyncMock(
        return_value=[
            {
                "document_id": "doc-1",
                "content": "Manual interno de estoque recomenda revisar cobertura e margem semanalmente.",
                "metadata": {"filename": "manual-interno.txt", "url": "javascript:alert(1)"},
                "score": 0.91,
            }
        ]
    )
    service._index_memory_message = AsyncMock()

    agent = Mock()
    agent.run_async = AsyncMock(return_value={"response": "Resposta baseada em conhecimento interno."})
    service._agents_by_role["analyst"] = agent

    response = await service.process_message(
        query="Qual a política interna para cobertura de estoque?",
        session_id="sess-current",
        user_id="12345678-1234-1234-1234-123456789012",
        user_role="analyst",
    )

    called_history = agent.run_async.await_args.args[1]
    assert service._retrieve_document_context.await_args.kwargs["session_id"] == "sess-current"

    assert called_history[0]["role"] == "system"
    assert "manual-interno.txt" in called_history[0]["content"]
    assert "Resposta baseada em conhecimento interno." in response["result"]["mensagem"]
    assert response["source"] == "rag.internal_documents"
    assert response["citations"][0]["source"] == "manual-interno.txt"
    assert "url" not in response["citations"][0]


@pytest.mark.asyncio
async def test_retrieve_document_context_prioritizes_same_session_attachments():
    session_manager = Mock(spec=SessionManager)
    service = ChatServiceV3(session_manager=session_manager)
    service.vectorization_agent = None
    service.vector_memory_repository = Mock()
    service.vector_memory_repository.hybrid_document_search = AsyncMock(return_value=[])
    service.vector_memory_repository.list_recent_documents = AsyncMock(
        return_value=[
            {
                "document_id": "doc-session",
                "content": "Arquivo anexado com margem consolidada por loja e cobertura semanal.",
                "metadata": {
                    "filename": "margem-loja.csv",
                    "session_id": "sess-current",
                    "uploaded_by": "user-1",
                },
                "score": 0.0,
            },
            {
                "document_id": "doc-other-user",
                "content": "Arquivo de outro usuario.",
                "metadata": {
                    "filename": "restrito.csv",
                    "session_id": "sess-current",
                    "uploaded_by": "user-2",
                },
                "score": 0.0,
            },
        ]
    )

    results = await service._retrieve_document_context(
        query="Analise o arquivo anexado desta sessao.",
        user_id="user-1",
        session_id="sess-current",
        tenant_id="default",
    )

    assert len(results) == 1
    assert results[0]["document_id"] == "doc-session"
    assert results[0]["metadata"]["filename"] == "margem-loja.csv"


@pytest.mark.asyncio
async def test_process_message_uses_attachment_pipeline_for_basket_margin_without_calling_agent():
    session_manager = Mock(spec=SessionManager)
    session_manager.get_history.return_value = []
    session_manager.list_sessions.return_value = []

    service = ChatServiceV3(session_manager=session_manager)
    service._load_user_preferences = AsyncMock(return_value={})
    service._retrieve_cross_session_memory = AsyncMock(return_value=[])
    service._retrieve_document_context = AsyncMock(
        return_value=[
            {
                "document_id": "doc-cesta",
                "content": (
                    "sku,nome,quantidade,preco_unitario,custo_unitario,imposto_pct,frete_valor\n"
                    "CAN-001,Caneta Azul,10,4.90,2.10,8,4\n"
                    "CAD-001,Caderno,5,19.90,12.00,8,6\n"
                ),
                "metadata": {"filename": "cesta.csv"},
                "score": 0.98,
            }
        ]
    )
    service._index_memory_message = AsyncMock()

    agent = Mock()
    agent.run_async = AsyncMock(return_value={"response": "fallback"})
    service._agents_by_role["analyst"] = agent

    response = await service.process_message(
        query="Calcule a margem real desta cesta anexada.",
        session_id="sess-current",
        user_id="12345678-1234-1234-1234-123456789012",
        user_role="analyst",
    )

    agent.run_async.assert_not_awaited()
    assert response["source"] == "tool.analisar_cesta_compras"
    assert response["mode"] == "attachment_basket_pipeline"
    assert response["tool_calls"][0]["name"] == "analisar_cesta_compras"
    assert "margem real" in response["result"]["mensagem"].lower()
    assert response["citations"][0]["source"] == "cesta.csv"


@pytest.mark.asyncio
async def test_process_message_uses_attachment_pipeline_for_market_basket_on_generic_prompt():
    session_manager = Mock(spec=SessionManager)
    session_manager.get_history.return_value = []
    session_manager.list_sessions.return_value = []

    service = ChatServiceV3(session_manager=session_manager)
    service._load_user_preferences = AsyncMock(return_value={})
    service._retrieve_cross_session_memory = AsyncMock(return_value=[])
    service._retrieve_document_context = AsyncMock(
        return_value=[
            {
                "document_id": "doc-market",
                "content": "pedido,produto\n1001,fralda\n1001,cerveja\n1002,fralda\n1002,lenco\n",
                "metadata": {"filename": "market.csv"},
                "score": 0.98,
            }
        ]
    )
    service._index_memory_message = AsyncMock()

    agent = Mock()
    agent.run_async = AsyncMock(return_value={"response": "fallback"})
    service._agents_by_role["analyst"] = agent

    response = await service.process_message(
        query="Analise os arquivos anexados.",
        session_id="sess-current",
        user_id="12345678-1234-1234-1234-123456789012",
        user_role="analyst",
    )

    agent.run_async.assert_not_awaited()
    assert response["source"] == "tool.minerar_cestas_frequentes"
    assert response["mode"] == "attachment_basket_pipeline"
    assert response["tool_calls"][0]["name"] == "minerar_cestas_frequentes"
    assert response["table_data"]
