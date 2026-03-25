from types import SimpleNamespace
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
async def test_retrieve_document_context_does_not_pull_session_attachment_for_unrelated_query():
    session_manager = Mock(spec=SessionManager)
    service = ChatServiceV3(session_manager=session_manager)
    service.vectorization_agent = None
    service.vector_memory_repository = Mock()
    service.vector_memory_repository.hybrid_document_search = AsyncMock(return_value=[])
    service.vector_memory_repository.list_recent_documents = AsyncMock(
        return_value=[
            {
                "document_id": "doc-session",
                "content": "Arquivo anexado com basket e vendas por loja.",
                "metadata": {
                    "filename": "csv_basket_realista_baseado_no_parquet_12000_linhas.csv",
                    "session_id": "sess-current",
                    "uploaded_by": "user-1",
                },
                "score": 0.0,
            }
        ]
    )

    results = await service._retrieve_document_context(
        query=(
            "me gere um gráfico de vendas do produto 369947 em todas as lojas\n\n"
            "Considere os anexos desta sessão: csv_basket_realista_baseado_no_parquet_12000_linhas.csv."
        ),
        user_id="user-1",
        session_id="sess-current",
        tenant_id="default",
    )

    assert results == []
    service.vector_memory_repository.list_recent_documents.assert_not_awaited()


@pytest.mark.asyncio
async def test_retrieve_document_context_filters_attachment_from_hybrid_results_for_unrelated_query():
    session_manager = Mock(spec=SessionManager)
    service = ChatServiceV3(session_manager=session_manager)
    service.vectorization_agent = None
    service.vector_memory_repository = Mock()
    service.vector_memory_repository.hybrid_document_search = AsyncMock(
        return_value=[
            {
                "document_id": "doc-session",
                "content": "Arquivo anexado com basket e vendas por loja.",
                "metadata": {
                    "filename": "csv_basket_realista_baseado_no_parquet_12000_linhas.csv",
                    "session_id": "sess-current",
                    "uploaded_by": "user-1",
                    "uploaded_via": "chat_attachment",
                },
                "score": 0.93,
            }
        ]
    )
    service.vector_memory_repository.list_recent_documents = AsyncMock(return_value=[])

    results = await service._retrieve_document_context(
        query="me gere um gráfico de vendas do produto 369947 em todas as lojas",
        user_id="user-1",
        session_id="sess-current",
        tenant_id="default",
    )

    assert results == []
    service.vector_memory_repository.list_recent_documents.assert_not_awaited()


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


@pytest.mark.asyncio
async def test_process_message_ignores_attachment_filename_csv_for_automation_and_runs_basket_pipeline():
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
                "metadata": {"filename": "csv_basket_realista_baseado_no_parquet_12000_linhas.csv"},
                "score": 0.98,
            }
        ]
    )
    service._index_memory_message = AsyncMock()

    agent = Mock()
    agent.run_async = AsyncMock(return_value={"response": "fallback"})
    service._agents_by_role["analyst"] = agent

    response = await service.process_message(
        query=(
            "Quais produtos costumam ser comprados juntos?\n\n"
            "Considere os anexos desta sessão: csv_basket_realista_baseado_no_parquet_12000_linhas.csv."
        ),
        session_id="sess-current",
        user_id="12345678-1234-1234-1234-123456789012",
        user_role="analyst",
    )

    agent.run_async.assert_not_awaited()
    assert response["source"] == "tool.minerar_cestas_frequentes"
    assert response["mode"] == "attachment_basket_pipeline"
    assert response["tool_calls"][0]["name"] == "minerar_cestas_frequentes"


@pytest.mark.asyncio
async def test_process_message_does_not_route_graph_query_to_basket_pipeline_due_to_attachment_filename():
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
                "content": "transaction_id,produto,valor_unitario\n500001,ZIPER,9.99\n500001,FITA CETIM,49.90\n",
                "metadata": {"filename": "csv_basket_realista_baseado_no_parquet_12000_linhas.csv"},
                "score": 0.98,
            }
        ]
    )
    service._index_memory_message = AsyncMock()

    agent = Mock()
    agent.run_async = AsyncMock(return_value={"response": "fallback-grafico"})
    service._agents_by_role["analyst"] = agent

    response = await service.process_message(
        query=(
            "me gere um gráfico de vendas do produto 369947 em todas as lojas\n\n"
            "Considere os anexos desta sessão: csv_basket_realista_baseado_no_parquet_12000_linhas.csv."
        ),
        session_id="sess-current",
        user_id="12345678-1234-1234-1234-123456789012",
        user_role="analyst",
    )

    agent.run_async.assert_awaited_once()
    assert response["source"] == "policy.response_validation"
    assert response["mode"] == "validation_block"
    assert response["result"]["mensagem"].startswith("## Resumo executivo")
    assert "visualização confiável" in response["result"]["mensagem"].lower()


@pytest.mark.asyncio
async def test_process_message_recovers_visualization_when_agent_returns_plain_text(monkeypatch):
    session_manager = Mock(spec=SessionManager)
    session_manager.get_history.return_value = []
    session_manager.list_sessions.return_value = []

    service = ChatServiceV3(session_manager=session_manager)
    service._load_user_preferences = AsyncMock(return_value={})
    service._retrieve_cross_session_memory = AsyncMock(return_value=[])
    service._retrieve_document_context = AsyncMock(return_value=[])
    service._index_memory_message = AsyncMock()

    monkeypatch.setattr(
        "backend.app.core.utils.intent_classifier.classify_intent",
        lambda query: SimpleNamespace(intent=SimpleNamespace(value="visualization"), confidence=0.95, matched_patterns=[]),
    )
    monkeypatch.setattr(
        "backend.app.core.utils.query_router.route_query",
        lambda intent, query, confidence: SimpleNamespace(
            tool_name="gerar_grafico_universal_v2",
            tool_params={"descricao": query, "tipo_grafico": "bar", "limite": 50},
            confidence=0.95,
            fallback_tools=[],
            reasoning="visualization recovery",
        ),
    )

    agent = Mock()
    agent.run_async = AsyncMock(return_value={"response": "Posso analisar isso para você."})
    agent._resolve_query_with_history_context = Mock(side_effect=lambda query, history: query)
    agent._enrich_tool_selection_for_business = Mock()
    agent._ensure_tool_selection_available = Mock()
    agent._build_clarification_if_needed = Mock(return_value=None)
    agent._attempt_routed_tool_rescue = AsyncMock(
        return_value={
            "response": "Gráfico gerado com sucesso.",
            "source": "tool.gerar_grafico_universal_v2",
            "chart_data": {"type": "bar", "labels": ["64", "2475"], "datasets": [{"data": [12, 8]}]},
            "tool_calls": [{"function": {"name": "gerar_grafico_universal_v2"}}],
        }
    )
    service._agents_by_role["analyst"] = agent

    response = await service.process_message(
        query="gere um gráfico de vendas do produto 369947 em todas as lojas",
        session_id="sess-chart",
        user_id="12345678-1234-1234-1234-123456789012",
        user_role="analyst",
    )

    agent.run_async.assert_awaited_once()
    agent._attempt_routed_tool_rescue.assert_awaited_once()
    assert response["source"] == "tool.gerar_grafico_universal_v2"
    assert response.get("chart_data")


@pytest.mark.asyncio
async def test_process_message_recovers_table_when_agent_returns_plain_text(monkeypatch):
    session_manager = Mock(spec=SessionManager)
    session_manager.get_history.return_value = []
    session_manager.list_sessions.return_value = []

    service = ChatServiceV3(session_manager=session_manager)
    service._load_user_preferences = AsyncMock(return_value={})
    service._retrieve_cross_session_memory = AsyncMock(return_value=[])
    service._retrieve_document_context = AsyncMock(return_value=[])
    service._index_memory_message = AsyncMock()

    monkeypatch.setattr(
        "backend.app.core.utils.intent_classifier.classify_intent",
        lambda query: SimpleNamespace(intent=SimpleNamespace(value="data_query"), confidence=0.91, matched_patterns=[]),
    )
    monkeypatch.setattr(
        "backend.app.core.utils.query_router.route_query",
        lambda intent, query, confidence: SimpleNamespace(
            tool_name="consultar_dados_flexivel",
            tool_params={
                "agregacao": "SUM",
                "coluna_agregacao": "VENDA_30DD",
                "agrupar_por": ["UNE"],
                "ordenar_por": "valor",
                "ordem_desc": True,
                "limite": 10,
                "filtros": {"NOMESEGMENTO": "TECIDOS"},
            },
            confidence=0.91,
            fallback_tools=[],
            reasoning="table recovery",
        ),
    )

    agent = Mock()
    agent.run_async = AsyncMock(return_value={"response": "Consolidei a analise e posso resumir em texto."})
    agent._resolve_query_with_history_context = Mock(side_effect=lambda query, history: query)
    agent._enrich_tool_selection_for_business = Mock()
    agent._ensure_tool_selection_available = Mock()
    agent._build_clarification_if_needed = Mock(return_value=None)
    agent._attempt_routed_tool_rescue = AsyncMock(
        return_value={
            "response": "Tabela gerada com sucesso.",
            "source": "tool.consultar_dados_flexivel",
            "table_data": [
                {"Loja (UNE)": "1685", "Venda (R$)": 311492.84, "Ranking": 1},
                {"Loja (UNE)": "520", "Venda (R$)": 154720.52, "Ranking": 2},
            ],
            "tool_calls": [{"function": {"name": "consultar_dados_flexivel"}}],
        }
    )
    service._agents_by_role["analyst"] = agent

    response = await service.process_message(
        query="me mostre em tabela as vendas por loja do segmento tecidos nos ultimos 30 dias",
        session_id="sess-table",
        user_id="12345678-1234-1234-1234-123456789012",
        user_role="analyst",
    )

    agent.run_async.assert_awaited_once()
    agent._attempt_routed_tool_rescue.assert_awaited_once()
    assert response["source"] == "tool.consultar_dados_flexivel"
    assert isinstance(response.get("table_data"), list)
    assert len(response["table_data"]) == 2


@pytest.mark.asyncio
async def test_process_message_recovers_table_even_when_agent_initially_returns_no_data_text(monkeypatch):
    session_manager = Mock(spec=SessionManager)
    session_manager.get_history.return_value = []
    session_manager.list_sessions.return_value = []

    service = ChatServiceV3(session_manager=session_manager)
    service._load_user_preferences = AsyncMock(return_value={})
    service._retrieve_cross_session_memory = AsyncMock(return_value=[])
    service._retrieve_document_context = AsyncMock(return_value=[])
    service._index_memory_message = AsyncMock()

    monkeypatch.setattr(
        "backend.app.core.utils.intent_classifier.classify_intent",
        lambda query: SimpleNamespace(intent=SimpleNamespace(value="data_query"), confidence=0.91, matched_patterns=[]),
    )
    monkeypatch.setattr(
        "backend.app.core.utils.query_router.route_query",
        lambda intent, query, confidence: SimpleNamespace(
            tool_name="consultar_dados_flexivel",
            tool_params={
                "agregacao": "SUM",
                "coluna_agregacao": "VENDA_30DD",
                "agrupar_por": ["UNE"],
                "ordenar_por": "valor",
                "ordem_desc": True,
                "limite": 10,
                "filtros": {"NOMESEGMENTO": "TECIDOS"},
            },
            confidence=0.91,
            fallback_tools=[],
            reasoning="table recovery after no_data",
        ),
    )

    agent = Mock()
    agent.run_async = AsyncMock(
        return_value={
            "response": "Nao consegui montar uma tabela confiavel para este pedido nesta rodada.",
            "source": "llm.direct",
        }
    )
    agent._resolve_query_with_history_context = Mock(side_effect=lambda query, history: query)
    agent._enrich_tool_selection_for_business = Mock()
    agent._ensure_tool_selection_available = Mock()
    agent._build_clarification_if_needed = Mock(return_value=None)
    agent._attempt_routed_tool_rescue = AsyncMock(
        return_value={
            "response": "Tabela gerada com sucesso.",
            "source": "tool.consultar_dados_flexivel",
            "table_data": [
                {"Loja (UNE)": "1685", "Venda (R$)": 311492.84, "Ranking": 1},
            ],
            "tool_calls": [{"function": {"name": "consultar_dados_flexivel"}}],
        }
    )
    service._agents_by_role["analyst"] = agent

    response = await service.process_message(
        query="me mostre em tabela as vendas por loja do segmento tecidos nos ultimos 30 dias",
        session_id="sess-table-recovery",
        user_id="12345678-1234-1234-1234-123456789012",
        user_role="analyst",
    )

    agent._attempt_routed_tool_rescue.assert_awaited_once()
    assert response["source"] == "tool.consultar_dados_flexivel"
    assert response.get("table_data")


@pytest.mark.asyncio
async def test_process_message_strips_automatic_attachment_suffix_before_calling_agent():
    session_manager = Mock(spec=SessionManager)
    session_manager.get_history.return_value = []
    session_manager.list_sessions.return_value = []

    service = ChatServiceV3(session_manager=session_manager)
    service._load_user_preferences = AsyncMock(return_value={})
    service._retrieve_cross_session_memory = AsyncMock(return_value=[])
    service._retrieve_document_context = AsyncMock(return_value=[])
    service._index_memory_message = AsyncMock()

    agent = Mock()
    agent.run_async = AsyncMock(return_value={"response": "ok"})
    service._agents_by_role["analyst"] = agent

    await service.process_message(
        query=(
            "me gere um gráfico de vendas do produto 369947 em todas as lojas\n\n"
            "Considere os anexos desta sessão: csv_basket_realista_baseado_no_parquet_12000_linhas.csv."
        ),
        session_id="sess-strip",
        user_id="12345678-1234-1234-1234-123456789012",
        user_role="analyst",
    )

    called_query = agent.run_async.await_args.args[0]
    assert called_query == "me gere um gráfico de vendas do produto 369947 em todas as lojas"


@pytest.mark.asyncio
async def test_same_chat_can_answer_attachment_basket_then_graph_and_operational_queries():
    session_manager = Mock(spec=SessionManager)
    session_manager.get_history.return_value = []
    session_manager.list_sessions.return_value = []

    service = ChatServiceV3(session_manager=session_manager)
    service._load_user_preferences = AsyncMock(return_value={})
    service._retrieve_cross_session_memory = AsyncMock(return_value=[])
    service._index_memory_message = AsyncMock()
    service.vectorization_agent = None
    service.vector_memory_repository = Mock()
    service.vector_memory_repository.hybrid_document_search = AsyncMock(return_value=[])
    service.vector_memory_repository.list_recent_documents = AsyncMock(
        return_value=[
            {
                "document_id": "doc-attachment",
                "content": (
                    "transaction_id,produto,valor_unitario\n"
                    "500001,CADERNO UNIVERSITARIO,12.90\n"
                    "500001,CANETA AZUL,12.90\n"
                    "500002,TINTA GUACHE,7.50\n"
                    "500002,PINCEL CHATO,5.90\n"
                ),
                "metadata": {
                    "filename": "csv_basket_realista_baseado_no_parquet_12000_linhas.csv",
                    "session_id": "sess-multi-turn",
                    "uploaded_by": "12345678-1234-1234-1234-123456789012",
                    "uploaded_via": "chat_attachment",
                },
                "score": 0.99,
            }
        ]
    )

    agent = Mock()
    agent.run_async = AsyncMock(
        side_effect=[
            {
                "response": "Gráfico gerado com sucesso.",
                "source": "tool.gerar_grafico_universal_v2",
                "chart_data": {
                    "type": "bar",
                    "labels": ["64", "2475"],
                    "datasets": [{"data": [12, 8]}],
                },
                "tool_calls": [{"function": {"name": "gerar_grafico_universal_v2"}}],
            },
            {
                "response": "A UNE 64 lidera as vendas do produto 369947 e a UNE 2475 está abaixo da média.",
                "source": "tool.analisar_produto_todas_lojas",
                "tool_calls": [{"function": {"name": "analisar_produto_todas_lojas"}}],
            },
        ]
    )
    service._agents_by_role["analyst"] = agent

    basket_response = await service.process_message(
        query="quais produtos costumam ser comprados juntos neste anexo?",
        session_id="sess-multi-turn",
        user_id="12345678-1234-1234-1234-123456789012",
        user_role="analyst",
    )
    chart_response = await service.process_message(
        query=(
            "me gere um gráfico de vendas do produto 369947 em todas as lojas\n\n"
            "Considere os anexos desta sessão: csv_basket_realista_baseado_no_parquet_12000_linhas.csv."
        ),
        session_id="sess-multi-turn",
        user_id="12345678-1234-1234-1234-123456789012",
        user_role="analyst",
    )
    operational_response = await service.process_message(
        query="agora me diga quais lojas vendem melhor o produto 369947",
        session_id="sess-multi-turn",
        user_id="12345678-1234-1234-1234-123456789012",
        user_role="analyst",
    )

    assert basket_response["source"] == "tool.minerar_cestas_frequentes"
    assert basket_response["mode"] == "attachment_basket_pipeline"
    assert basket_response["citations"][0]["source"] == "csv_basket_realista_baseado_no_parquet_12000_linhas.csv"

    assert chart_response["source"] == "tool.gerar_grafico_universal_v2"
    assert chart_response.get("chart_data")
    assert chart_response.get("citations") in (None, [])

    assert operational_response["source"] == "tool.analisar_produto_todas_lojas"
    assert operational_response.get("citations") in (None, [])

    assert agent.run_async.await_count == 2
    chart_query = agent.run_async.await_args_list[0].args[0]
    operational_query = agent.run_async.await_args_list[1].args[0]
    assert chart_query == "me gere um gráfico de vendas do produto 369947 em todas as lojas"
    assert operational_query == "agora me diga quais lojas vendem melhor o produto 369947"
    assert service.vector_memory_repository.list_recent_documents.await_count == 1


@pytest.mark.asyncio
async def test_process_message_blocks_visualization_response_without_visual_payload():
    session_manager = Mock(spec=SessionManager)
    session_manager.get_history.return_value = []
    session_manager.list_sessions.return_value = []

    service = ChatServiceV3(session_manager=session_manager)
    service._load_user_preferences = AsyncMock(return_value={})
    service._retrieve_cross_session_memory = AsyncMock(return_value=[])
    service._retrieve_document_context = AsyncMock(return_value=[])
    service._index_memory_message = AsyncMock()

    agent = Mock()
    agent.run_async = AsyncMock(
        return_value={
            "response": "Segue a análise textual das vendas do produto 369947.",
            "source": "tool.gerar_grafico_universal_v2",
            "mode": "deterministic_tool",
        }
    )
    service._agents_by_role["analyst"] = agent

    response = await service.process_message(
        query="me gere um gráfico de vendas do produto 369947 em todas as lojas",
        session_id="sess-chart-block",
        user_id="12345678-1234-1234-1234-123456789012",
        user_role="analyst",
    )

    assert response["source"] == "policy.response_validation"
    assert response["mode"] == "validation_block"
    assert "visualização confiável" in response["result"]["mensagem"].lower()


@pytest.mark.asyncio
async def test_process_message_keeps_honest_chart_failure_instead_of_policy_block():
    session_manager = Mock(spec=SessionManager)
    session_manager.get_history.return_value = []
    session_manager.list_sessions.return_value = []

    service = ChatServiceV3(session_manager=session_manager)
    service._load_user_preferences = AsyncMock(return_value={})
    service._retrieve_cross_session_memory = AsyncMock(return_value=[])
    service._retrieve_document_context = AsyncMock(return_value=[])
    service._index_memory_message = AsyncMock()

    agent = Mock()
    agent.run_async = AsyncMock(
        return_value={
            "response": "Não consegui gerar o gráfico: Não encontrei dados para montar o gráfico nesse recorte.",
            "source": "tool.gerar_grafico_universal_v2",
            "mode": "deterministic_tool",
            "confidence": 0.74,
        }
    )
    service._agents_by_role["analyst"] = agent

    response = await service.process_message(
        query="gere um gráfico de vendas dos segmentos da une 520",
        session_id="sess-chart-no-data",
        user_id="12345678-1234-1234-1234-123456789012",
        user_role="analyst",
    )

    assert response["source"] == "tool.gerar_grafico_universal_v2"
    assert response["mode"] == "deterministic_tool"
    assert "não consegui gerar o gráfico" in response["result"]["mensagem"].lower()


@pytest.mark.asyncio
async def test_process_message_blocks_market_research_without_citations():
    session_manager = Mock(spec=SessionManager)
    session_manager.get_history.return_value = []
    session_manager.list_sessions.return_value = []

    service = ChatServiceV3(session_manager=session_manager)
    service._load_user_preferences = AsyncMock(return_value={})
    service._retrieve_cross_session_memory = AsyncMock(return_value=[])
    service._retrieve_document_context = AsyncMock(return_value=[])
    service._index_memory_message = AsyncMock()

    agent = Mock()
    agent.run_async = AsyncMock(
        return_value={
            "response": "Encontrei um preço médio de mercado para o item solicitado.",
            "source": "tool.pesquisar_mercado_web",
            "mode": "deterministic_tool",
            "confidence": 0.82,
        }
    )
    service._agents_by_role["analyst"] = agent

    response = await service.process_message(
        query="faça uma pesquisa de mercado do produto cola quente",
        session_id="sess-market-block",
        user_id="12345678-1234-1234-1234-123456789012",
        user_role="analyst",
    )

    assert response["source"] == "policy.response_validation"
    assert response["mode"] == "validation_block"
    assert "evidência pública" in response["result"]["mensagem"].lower()


@pytest.mark.asyncio
async def test_process_message_blocks_dashboard_without_dashboard_payload():
    session_manager = Mock(spec=SessionManager)
    session_manager.get_history.return_value = []
    session_manager.list_sessions.return_value = []

    service = ChatServiceV3(session_manager=session_manager)
    service._load_user_preferences = AsyncMock(return_value={})
    service._retrieve_cross_session_memory = AsyncMock(return_value=[])
    service._retrieve_document_context = AsyncMock(return_value=[])
    service._index_memory_message = AsyncMock()

    agent = Mock()
    agent.run_async = AsyncMock(
        return_value={
            "response": "Preparei um painel executivo para as lojas.",
            "source": "tool.dashboard",
            "mode": "deterministic_tool",
            "confidence": 0.84,
        }
    )
    service._agents_by_role["analyst"] = agent

    response = await service.process_message(
        query="monte um dashboard de vendas por loja",
        session_id="sess-dashboard-block",
        user_id="12345678-1234-1234-1234-123456789012",
        user_role="analyst",
    )

    assert response["source"] == "policy.response_validation"
    assert response["mode"] == "validation_block"
    assert "dashboard" in response["result"]["mensagem"].lower()
    assert "dashboard_spec" in response["result"]["mensagem"].lower()


@pytest.mark.asyncio
async def test_process_message_blocks_table_without_table_payload():
    session_manager = Mock(spec=SessionManager)
    session_manager.get_history.return_value = []
    session_manager.list_sessions.return_value = []

    service = ChatServiceV3(session_manager=session_manager)
    service._load_user_preferences = AsyncMock(return_value={})
    service._retrieve_cross_session_memory = AsyncMock(return_value=[])
    service._retrieve_document_context = AsyncMock(return_value=[])
    service._index_memory_message = AsyncMock()

    agent = Mock()
    agent.run_async = AsyncMock(
        return_value={
            "response": "Segue o consolidado executivo por loja.",
            "source": "tool.consultar_dados_flexivel",
            "mode": "deterministic_tool",
            "confidence": 0.88,
        }
    )
    service._agents_by_role["analyst"] = agent

    response = await service.process_message(
        query="me mostre em tabela as vendas por loja",
        session_id="sess-table-block",
        user_id="12345678-1234-1234-1234-123456789012",
        user_role="analyst",
    )

    assert response["source"] == "policy.response_validation"
    assert response["mode"] == "validation_block"
    assert "table_data" in response["result"]["mensagem"]


@pytest.mark.asyncio
async def test_process_message_blocks_export_without_export_payload():
    session_manager = Mock(spec=SessionManager)
    session_manager.get_history.return_value = []
    session_manager.list_sessions.return_value = []

    service = ChatServiceV3(session_manager=session_manager)
    service._load_user_preferences = AsyncMock(return_value={})
    service._retrieve_cross_session_memory = AsyncMock(return_value=[])
    service._retrieve_document_context = AsyncMock(return_value=[])
    service._index_memory_message = AsyncMock()

    agent = Mock()
    agent.run_async = AsyncMock(
        return_value={
            "response": "Consolidei os dados e posso seguir com a exportação.",
            "source": "tool.consultar_dados_flexivel",
            "mode": "deterministic_tool",
            "confidence": 0.8,
        }
    )
    service._agents_by_role["analyst"] = agent

    response = await service.process_message(
        query="exporte um csv de vendas por loja",
        session_id="sess-export-block",
        user_id="12345678-1234-1234-1234-123456789012",
        user_role="analyst",
    )

    assert response["source"] == "policy.response_validation"
    assert response["mode"] == "validation_block"
    assert "exportação" in response["result"]["mensagem"].lower()


@pytest.mark.asyncio
async def test_process_message_blocks_wrong_basket_pipeline_for_non_basket_query():
    session_manager = Mock(spec=SessionManager)
    session_manager.get_history.return_value = []
    session_manager.list_sessions.return_value = []

    service = ChatServiceV3(session_manager=session_manager)
    service._load_user_preferences = AsyncMock(return_value={})
    service._retrieve_cross_session_memory = AsyncMock(return_value=[])
    service._retrieve_document_context = AsyncMock(return_value=[])
    service._index_memory_message = AsyncMock()

    agent = Mock()
    agent.run_async = AsyncMock(
        return_value={
            "response": "Encontrei relações frequentes entre itens no arquivo.",
            "source": "tool.minerar_cestas_frequentes",
            "mode": "attachment_basket_pipeline",
        }
    )
    service._agents_by_role["analyst"] = agent

    response = await service.process_message(
        query="me gere um gráfico de vendas do produto 369947 em todas as lojas",
        session_id="sess-wrong-basket-block",
        user_id="12345678-1234-1234-1234-123456789012",
        user_role="analyst",
    )

    assert response["source"] == "policy.response_validation"
    assert response["mode"] == "validation_block"
    assert "pipeline especializado incompatível" in response["result"]["mensagem"].lower()


@pytest.mark.asyncio
async def test_process_message_blocks_wrong_basket_pipeline_for_export_query():
    session_manager = Mock(spec=SessionManager)
    session_manager.get_history.return_value = []
    session_manager.list_sessions.return_value = []

    service = ChatServiceV3(session_manager=session_manager)
    service._load_user_preferences = AsyncMock(return_value={})
    service._retrieve_cross_session_memory = AsyncMock(return_value=[])
    service._retrieve_document_context = AsyncMock(return_value=[])
    service._index_memory_message = AsyncMock()

    agent = Mock()
    agent.run_async = AsyncMock(
        return_value={
            "response": "Encontrei relações frequentes entre itens no arquivo.",
            "source": "tool.minerar_cestas_frequentes",
            "mode": "attachment_basket_pipeline",
        }
    )
    service._agents_by_role["analyst"] = agent

    response = await service.process_message(
        query="exporte um csv com as vendas por loja",
        session_id="sess-export-basket-block",
        user_id="12345678-1234-1234-1234-123456789012",
        user_role="analyst",
    )

    assert response["source"] == "policy.response_validation"
    assert response["mode"] == "validation_block"
    assert "exportação" in response["result"]["mensagem"].lower()
