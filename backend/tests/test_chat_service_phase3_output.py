from unittest.mock import Mock
from types import SimpleNamespace

from backend.app.core.context import set_current_user_context
from backend.app.core.utils.session_manager import SessionManager
from backend.app.services.chat_service_v3 import ChatServiceV3


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
    assert "## SQL/Python" in message
    assert "## Ação recomendada" in message or "## Acao recomendada" in message
    assert "## Recorte e evidência" in message or "## Recorte e evidencia" in message


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
            "## SQL/Python\n"
            "```sql\nSELECT * FROM admmat LIMIT 50;\n```\n\n"
            "## Ação recomendada\n"
            "- Priorizar plano comercial.\n\n"
            "## Recorte e evidência\n"
            "- Métrica: soma de vendas por UNE."
        ),
    }
    result = service._process_agent_response(
        agent_response,
        query="relatorio de vendas por une",
        user_role="user",
    )
    message = result["result"]["mensagem"]

    assert "Detalhamento por loja/UNE restrito para este perfil." in message
    assert "Conteudo tecnico restrito para este perfil." in message
    assert "SELECT * FROM admmat" not in message
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
            "## SQL/Python\n"
            "```sql\nSELECT * FROM admmat LIMIT 50;\n```\n\n"
            "## Ação recomendada\n"
            "- Priorizar plano comercial.\n\n"
            "## Recorte e evidência\n"
            "- Métrica: soma de vendas por UNE."
        ),
    }
    result = service._process_agent_response(
        agent_response,
        query="relatorio de vendas por une",
        user_role="admin",
    )
    message = result["result"]["mensagem"]

    assert "| Loja (UNE) | Venda (R$) |" in message
    assert "SELECT * FROM admmat LIMIT 50;" in message
    assert "Detalhamento por loja/UNE restrito para este perfil." not in message


def test_get_user_filters_uses_current_user_context_segments():
    session_manager = Mock(spec=SessionManager)
    service = ChatServiceV3(session_manager=session_manager)

    set_current_user_context(SimpleNamespace(id="u1", role="user", segments_list=["ARTES"]))
    filters = service._get_user_filters("u1")

    assert filters["segments"] == ["ARTES"]
    assert filters["rls_applied"] is True


def test_get_user_filters_admin_returns_full_access():
    session_manager = Mock(spec=SessionManager)
    service = ChatServiceV3(session_manager=session_manager)

    set_current_user_context(SimpleNamespace(id="admin1", role="admin", segments_list=["*"]))
    filters = service._get_user_filters("admin1")

    assert filters["segments"] == ["*"]
    assert filters["rls_applied"] is False
