from datetime import datetime

from backend.app.core.learning.chat_example_capture import build_chat_example_payload


def test_build_chat_example_payload_accepts_successful_chart_response():
    payload = build_chat_example_payload(
        query="quero um gráfico de vendas do segmento tecidos de cada loja",
        user_id="user-1",
        response={
            "type": "text",
            "result": {"mensagem": "Análise concluída com visualização gerada."},
            "chart_data": {"type": "bar", "labels": ["1685"], "datasets": [{"data": [311492.84]}]},
            "source": "tool.consultar_dados_flexivel",
            "confidence": 0.91,
            "tool_calls": [{"function": {"name": "consultar_dados_flexivel"}}],
        },
        assistant_metadata={
            "request_id": "req-123",
            "context": {
                "response_type": "chart",
                "has_chart": True,
                "segment": "TECIDOS",
                "response_breakdown": "loja",
            }
        },
        timestamp=datetime(2026, 3, 8, 16, 0, 0),
    )

    assert payload is not None
    assert payload["example_id"] == "req-123"
    assert payload["intent"] == "visualization"
    assert payload["assistant_response"] == "Análise concluída com visualização gerada."
    assert payload["metadata"]["response_type"] == "chart"
    assert "TECIDOS" in payload["metadata"]["tags"]
    assert payload["metadata"]["has_chart"] is True


def test_build_chat_example_payload_skips_degraded_no_data_response():
    payload = build_chat_example_payload(
        query="me de o gráfico de vendas do segmento tecidos de cada loja",
        user_id="user-1",
        assistant_text="Não consegui gerar o gráfico: Não encontrei dados para montar o gráfico nesse recorte.",
        assistant_metadata={
            "request_id": "req-456",
            "source": "tool.gerar_grafico_universal_v2",
            "context": {"response_type": "chart", "has_chart": False},
        },
    )

    assert payload is None


def test_build_chat_example_payload_skips_policy_and_automation_response():
    payload = build_chat_example_payload(
        query="envie um email com o relatório",
        user_id="user-1",
        response={
            "type": "text",
            "result": {"mensagem": "Solicitação pronta para aprovação."},
            "automation_request": {"action": "email.send"},
            "source": "automation.proposal",
            "mode": "automation_pending_approval",
        },
        assistant_metadata={
            "request_id": "req-789",
            "context": {"response_type": "text", "has_automation": True},
        },
    )

    assert payload is None
