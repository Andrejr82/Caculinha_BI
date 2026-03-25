import asyncio
from unittest.mock import AsyncMock, Mock
from types import SimpleNamespace

from backend.app.core.context import set_current_user_context
from backend.app.core.utils.session_manager import SessionManager
from backend.app.services.chat_service_v3 import ChatServiceV3


def _set_context_for_all_namespaces(user) -> None:
    set_current_user_context(user)
    try:
        from app.core.context import set_current_user_context as set_legacy_context
        set_legacy_context(user)
    except Exception:
        pass


def test_process_agent_response_applies_phase3_executive_format_for_business_query():
    session_manager = Mock(spec=SessionManager)
    service = ChatServiceV3(session_manager=session_manager)

    agent_response = {
        "response": "As vendas apresentaram variacao entre as unidades.",
    }
    result = service._process_agent_response(agent_response, query="analise vendas por une e segmento")
    message = result["result"]["mensagem"]

    assert "## Resumo executivo" in message
    assert "## Tabela operacional" in message
    assert "## Próximas ações" in message or "## Proximas acoes" in message
    assert "## SQL/Python" not in message
    assert "## Recorte e evidência" not in message


def test_process_agent_response_keeps_smalltalk_without_executive_wrapping():
    session_manager = Mock(spec=SessionManager)
    service = ChatServiceV3(session_manager=session_manager)

    agent_response = {"response": "Olá! Como posso ajudar?"}
    result = service._process_agent_response(agent_response, query="oi")
    message = result["result"]["mensagem"]

    assert message == "Olá! Como posso ajudar?"


def test_process_agent_response_redacts_internal_sections_for_restricted_role():
    session_manager = Mock(spec=SessionManager)
    service = ChatServiceV3(session_manager=session_manager)

    agent_response = {
        "response": (
            "## Resumo executivo\n"
            "- Total de vendas por UNE consolidado com sucesso. UNE líder: 1685.\n\n"
            "## Tabela operacional\n"
            "| Loja (UNE) | Venda (R$) |\n"
            "|---|---|\n"
            "| 1685 | 100,00 |\n\n"
            "## Próximas ações\n"
            "- Priorizar plano comercial.\n\n"
            "Fonte: deterministic_tool\n"
        ),
    }
    result = service._process_agent_response(
        agent_response,
        query="relatorio de vendas por une",
        user_role="user",
    )
    message = result["result"]["mensagem"]

    assert "Detalhamento por loja/UNE restrito para este perfil." in message
    assert "SQL/Python" not in message
    assert "Fonte:" not in message
    assert "UNE lider: [restrito]" in message


def test_process_agent_response_keeps_internal_sections_for_admin():
    session_manager = Mock(spec=SessionManager)
    service = ChatServiceV3(session_manager=session_manager)

    agent_response = {
        "response": (
            "## Resumo executivo\n"
            "- Total de vendas por UNE consolidado com sucesso. UNE líder: 1685.\n\n"
            "## Tabela operacional\n"
            "| Loja (UNE) | Venda (R$) |\n"
            "|---|---|\n"
            "| 1685 | 100,00 |\n\n"
            "## Próximas ações\n"
            "- Priorizar plano comercial.\n\n"
            "Fonte: deterministic_tool\n"
        ),
    }
    result = service._process_agent_response(
        agent_response,
        query="relatorio de vendas por une",
        user_role="admin",
    )
    message = result["result"]["mensagem"]

    assert "| Loja (UNE) | Venda (R$) |" in message
    assert "SQL/Python" not in message
    assert "Fonte:" not in message
    assert "Detalhamento por loja/UNE restrito para este perfil." not in message


def test_get_user_filters_uses_current_user_context_segments():
    session_manager = Mock(spec=SessionManager)
    service = ChatServiceV3(session_manager=session_manager)

    _set_context_for_all_namespaces(SimpleNamespace(id="u1", role="user", segments_list=["ARTES"]))
    filters = service._get_user_filters("u1")

    assert filters["segments"] == ["ARTES"]
    assert filters["rls_applied"] is True


def test_get_user_filters_admin_returns_full_access():
    session_manager = Mock(spec=SessionManager)
    service = ChatServiceV3(session_manager=session_manager)

    _set_context_for_all_namespaces(SimpleNamespace(id="admin1", role="admin", segments_list=["*"]))
    filters = service._get_user_filters("admin1")

    assert filters["segments"] == ["*"]
    assert filters["rls_applied"] is False


def test_process_agent_response_propagates_dashboard_contract_metadata():
    session_manager = Mock(spec=SessionManager)
    service = ChatServiceV3(session_manager=session_manager)

    dashboard_spec = {
        "title": "Dashboard Segmento ARTES",
        "filters": {"segmento": "ARTES", "periodo": "30d"},
        "widgets": [
            {"kind": "kpi", "id": "vendas_totais", "value": "120.000,00"},
            {"kind": "chart", "id": "visao_geral", "chart_spec": {"data": [], "layout": {}}},
            {"kind": "table", "id": "resumo_metricas", "rows": []},
        ],
    }
    agent_response = {
        "response": "Dashboard pronto.",
        "dashboard_spec": dashboard_spec,
        "source": "deterministic_tool",
        "confidence": 0.91,
    }

    result = service._process_agent_response(agent_response, query="dashboard do segmento artes")

    assert result["type"] == "dashboard"
    assert result["dashboard_spec"] == dashboard_spec
    assert "source" not in result
    assert "confidence" not in result


def test_process_agent_response_propagates_table_data_payload():
    session_manager = Mock(spec=SessionManager)
    service = ChatServiceV3(session_manager=session_manager)

    agent_response = {
        "response": "Analise pronta.",
        "table_data": [
            {"Cenario": "Base", "EOQ": "1000"},
            {"Cenario": "Demanda +20", "EOQ": "1095"},
        ],
    }

    result = service._process_agent_response(agent_response, query="faça análise de sensibilidade do eoq")

    assert result["type"] == "text"
    assert isinstance(result.get("table_data"), list)
    assert len(result["table_data"]) == 2


def test_process_agent_response_builds_enriched_sales_report_from_table_data():
    session_manager = Mock(spec=SessionManager)
    service = ChatServiceV3(session_manager=session_manager)

    agent_response = {
        "response": "Consolidei os dados de vendas por segmento.",
        "table_data": [
            {"NOMESEGMENTO": "PAPELARIA", "valor": 778096.0},
            {"NOMESEGMENTO": "TECIDOS", "valor": 610686.0},
            {"NOMESEGMENTO": "ARTES", "valor": 319947.0},
            {"NOMESEGMENTO": "AVIAMENTOS", "valor": 152340.0},
        ],
    }

    result = service._process_agent_response(
        agent_response,
        query="preciso de um relatório de vendas do segmento tecidos de todas as lojas",
    )
    message = result["result"]["mensagem"]

    assert "## Resumo executivo" in message
    assert "KPIs-chave" in message
    assert "| Segmento | Venda (R$) | Part. % | Ranking | Gap p/ média (R$) | Classificação |" in message
    assert "PAPELARIA" in message
    assert isinstance(result.get("table_data"), list)


def test_process_agent_response_propagates_image_and_audio_assets():
    session_manager = Mock(spec=SessionManager)
    service = ChatServiceV3(session_manager=session_manager)

    agent_response = {
        "response": "Conteúdo multimodal pronto.",
        "image_asset": {
            "url": "https://cdn.example.com/insight.png",
            "alt": "Mapa de calor de vendas",
        },
        "audio_asset": {
            "url": "https://cdn.example.com/resumo.mp3",
            "title": "Resumo narrado",
        },
    }

    result = service._process_agent_response(agent_response, query="gere um resumo multimodal")

    assert result["image_asset"]["url"] == "https://cdn.example.com/insight.png"
    assert result["audio_asset"]["url"] == "https://cdn.example.com/resumo.mp3"


def test_build_session_message_metadata_extracts_context_from_query_and_response():
    session_manager = Mock(spec=SessionManager)
    service = ChatServiceV3(session_manager=session_manager)

    response = {
        "type": "text",
        "result": {
            "mensagem": (
                "## Tabela operacional\n"
                "| Segmento | Vendas (R$) |\n"
                "|---|---|\n"
                "| PAPELARIA | 100,00 |"
            )
        },
        "_internal_meta": {"source": "deterministic_tool", "confidence": 0.91},
    }

    metadata = service.build_session_message_metadata(
        query="gere um gráfico de vendas de todos os segmentos em todas as unes",
        response=response,
        role="assistant",
    )

    assert metadata["context"]["query_breakdown"] == "SEGMENTO"
    assert metadata["context"]["response_breakdown"] == "SEGMENTO"
    assert metadata["context"]["scope_all_stores"] is True
    assert metadata["source"] == "deterministic_tool"


def test_build_session_message_metadata_persists_dashboard_context_and_source():
    session_manager = Mock(spec=SessionManager)
    service = ChatServiceV3(session_manager=session_manager)

    response = {
        "type": "dashboard",
        "dashboard_spec": {
            "title": "Dashboard Segmento ARTES",
            "filters": {"segmento": "ARTES", "periodo": "30d"},
            "widgets": [
                {"kind": "chart", "id": "visao_geral", "chart_spec": {"data": [], "layout": {}}},
            ],
        },
        "source": "deterministic_tool",
    }

    metadata = service.build_session_message_metadata(
        query="gere um dashboard interativo do segmento ARTES nos últimos 30 dias com tabela por UNE",
        response=response,
        role="assistant",
    )

    assert metadata["context"]["has_dashboard"] is True
    assert metadata["context"]["dashboard_title"] == "Dashboard Segmento ARTES"
    assert metadata["context"]["dashboard_filters"]["segmento"] == "ARTES"
    assert metadata["context"]["source"] == "deterministic_tool"


def test_build_session_message_metadata_persists_multimodal_assets():
    session_manager = Mock(spec=SessionManager)
    service = ChatServiceV3(session_manager=session_manager)

    response = {
        "type": "text",
        "result": {"mensagem": "Resumo multimodal pronto."},
        "image_asset": {"url": "https://cdn.example.com/insight.png", "alt": "Mapa"},
        "audio_asset": {"url": "https://cdn.example.com/resumo.mp3", "title": "Resumo"},
    }

    metadata = service.build_session_message_metadata(
        query="gere um resumo multimodal",
        response=response,
        role="assistant",
    )

    assert metadata["context"]["has_image"] is True
    assert metadata["context"]["has_audio"] is True
    assert metadata["ui_payload"]["image_asset"]["url"] == "https://cdn.example.com/insight.png"
    assert metadata["ui_payload"]["audio_asset"]["url"] == "https://cdn.example.com/resumo.mp3"


def test_build_session_message_metadata_persists_tool_names_and_latency():
    session_manager = Mock(spec=SessionManager)
    service = ChatServiceV3(session_manager=session_manager)

    response = {
        "type": "text",
        "result": {"mensagem": "Resumo com ferramentas."},
        "latency_seconds": 1.234,
        "tool_calls": [
            {"function": {"name": "consultar_dados_flexivel"}},
            {"function": {"name": "gerar_grafico_universal"}},
        ],
    }

    metadata = service.build_session_message_metadata(
        query="gere um resumo com gráfico",
        response=response,
        role="assistant",
    )

    assert metadata["tool_names"] == ["consultar_dados_flexivel", "gerar_grafico_universal"]
    assert metadata["tool_call_count"] == 2
    assert metadata["latency_seconds"] == 1.234
    assert metadata["context"]["latency_ms"] == 1234.0


def test_process_message_generates_image_asset_for_visual_prompt():
    session_manager = Mock(spec=SessionManager)
    session_manager.get_history.return_value = []
    session_manager.list_sessions.return_value = []
    service = ChatServiceV3(session_manager=session_manager)
    service._load_user_preferences = AsyncMock(return_value={})
    service._retrieve_document_context = AsyncMock(return_value=[])
    service._retrieve_cross_session_memory = AsyncMock(return_value=[])
    service._index_memory_message = AsyncMock()
    service.image_generation_service.generate_image = AsyncMock(
        return_value={
            "url": "data:image/svg+xml;base64,abc123",
            "alt": "gere uma imagem de ruptura",
            "prompt": "gere uma imagem de ruptura",
        }
    )

    response = asyncio.run(
        service.process_message(
            query="gere uma imagem conceitual de ruptura de estoque na loja",
            session_id="sess-image-gen",
            user_id="12345678-1234-1234-1234-123456789012",
            user_role="analyst",
        )
    )

    assert response["image_asset"]["url"].startswith("data:image/svg+xml;base64,")
    assert response["mode"] == "image_generation"


def test_build_session_message_metadata_persists_market_product_hint_and_competitors():
    session_manager = Mock(spec=SessionManager)
    service = ChatServiceV3(session_manager=session_manager)

    metadata = service.build_session_message_metadata(
        query="faça uma pesquisa de mercado do produto lapis de cor 12 cores na Kalunga e Amazon",
        role="user",
    )

    assert metadata["context"]["market_product_hint"] == "lapis de cor 12 cores"
    assert metadata["context"]["market_competitors"] == ["kalunga", "amazon"]
