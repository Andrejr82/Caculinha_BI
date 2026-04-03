import json

from backend.app.services.chat_service_v3 import ChatServiceV3


class _FakeLLM:
    def __init__(self, payload: str):
        self.payload = payload

    def generate_with_history(self, *args, **kwargs):
        return self.payload


def _bare_service(llm) -> ChatServiceV3:
    service = ChatServiceV3.__new__(ChatServiceV3)
    service.llm = llm
    return service


def test_generate_structured_executive_summary_uses_json_contract() -> None:
    service = _bare_service(
        _FakeLLM(
            json.dumps(
                {
                    "headline": "Margem pressionada em papelaria",
                    "summary": "A operacao precisa rever desconto e mix nas lojas com pior conversao.",
                    "key_findings": [
                        "A venda cresceu abaixo da expectativa nas lojas de menor cobertura.",
                        "O desconto atual reduz a margem sem ganho proporcional de volume.",
                    ],
                    "recommended_actions": [
                        "Revisar desconto por loja ainda nesta semana.",
                        "Repor itens de maior giro antes da proxima campanha.",
                    ],
                },
                ensure_ascii=False,
            )
        )
    )

    output = service._generate_structured_executive_summary(
        query="como esta a margem da promoção de papelaria?",
        message="Texto livre antigo",
        table_data=[{"UNE": 1685, "MARGEM": 22.4}],
    )

    assert "## Resumo executivo" in output
    assert "Margem pressionada em papelaria" in output
    assert "## Próximas ações" in output


def test_generate_structured_executive_summary_falls_back_to_original_text() -> None:
    service = _bare_service(_FakeLLM("not-json"))

    output = service._generate_structured_executive_summary(
        query="qual o resumo executivo das vendas?",
        message="Resumo livre existente",
        table_data=None,
    )

    assert output == "Resumo livre existente"
