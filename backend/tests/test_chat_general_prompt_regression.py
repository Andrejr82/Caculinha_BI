from backend.app.api.v1.endpoints.chat import _build_guided_chat_query
from backend.app.core.utils.response_validator import validate_response
from backend.app.services.chat_service_v3 import ChatServiceV3


def _service() -> ChatServiceV3:
    return object.__new__(ChatServiceV3)


def _guided(query: str) -> str:
    return _build_guided_chat_query(query, None, {"period": "ultimos 30 dias"}, None)


def _response(message: str, source: str = "llm.direct") -> dict:
    return {
        "type": "text",
        "result": {"mensagem": message},
        "source": source,
    }


def _executive_message(summary: str, ops: str, actions: str) -> str:
    return (
        "## Resumo executivo\n"
        f"- {summary}\n\n"
        "## Tabela operacional\n"
        f"- {ops}\n\n"
        "## Próximas ações\n"
        f"- {actions}"
    )


def test_general_prompt_regression_does_not_false_positive_market_research() -> None:
    service = _service()
    prompts = [
        "O que você consegue analisar sobre vendas, estoque, margem e ruptura neste sistema?",
        "Explique em linguagem simples a diferença entre faturamento, margem e giro de estoque.",
        "Compare papelaria entre as lojas 1685, 1974 e 2365 no último mês.",
        "Quais produtos estão em ruptura crítica agora?",
        "Liste as rupturas mais urgentes por loja e priorize as ações.",
        "Quais SKUs têm estoque baixo e venda alta nos últimos 15 dias?",
        "Analise a cesta de compras de papelaria e sugira oportunidades de cross-sell.",
        "Monte uma sugestão de combo para volta às aulas com foco em ticket médio.",
        "Faça uma previsão simples de demanda para itens sazonais de volta às aulas.",
        "Resuma executivamente o desempenho recente da operação.",
    ]

    for prompt in prompts:
        wrapped = _guided(prompt)
        capability = service._query_expected_capability(wrapped)
        assert capability != "market_research", prompt


def test_general_prompt_regression_plain_answers_are_not_blocked() -> None:
    service = _service()
    cases = [
        (
            "O que você consegue analisar sobre vendas, estoque, margem e ruptura neste sistema?",
            _response(
                _executive_message(
                    "Consigo analisar vendas, estoque, margem, ruptura e comparativos operacionais.",
                    "O sistema suporta leituras por loja, segmento, produto, preço, cobertura e performance recente.",
                    "Posso detalhar por período, produto, loja ou segmento conforme o recorte desejado.",
                )
            ),
        ),
        (
            "Explique em linguagem simples a diferença entre faturamento, margem e giro de estoque.",
            _response(
                _executive_message(
                    "Faturamento é quanto vendeu, margem é quanto sobra após custos e giro mede a velocidade do estoque.",
                    "Os três indicadores se complementam: vender muito sem margem destrói resultado e estoque parado reduz giro.",
                    "Se quiser, posso exemplificar cada um com números simples.",
                )
            ),
        ),
        (
            "Compare papelaria entre as lojas 1685, 1974 e 2365 no último mês.",
            _response(
                _executive_message(
                    "A comparação entre lojas pode ser feita por faturamento, margem, estoque e ruptura da papelaria.",
                    "O recorte por UNE e período é compatível com resposta analítica sem exigir pesquisa externa.",
                    "Posso detalhar líderes, cauda, gaps e recomendações por loja.",
                ),
                source="tool.consultar_dados_flexivel",
            ),
        ),
        (
            "Calcule o EOQ para um item de alta saída considerando demanda estável.",
            _response(
                _executive_message(
                    "O EOQ depende de demanda, custo de pedido e custo de armazenagem.",
                    "Sem esses insumos, a resposta correta é explicar a fórmula e pedir os parâmetros mínimos.",
                    "Informe demanda anual, custo por pedido e custo de armazenagem para calcular o lote econômico.",
                ),
                source="sandbox.code_gen_agent",
            ),
        ),
    ]

    for prompt, response in cases:
        wrapped = _guided(prompt)
        context = service._build_response_validation_context(wrapped, response)
        validation = validate_response(response, query=wrapped, context=context)
        assert validation.should_block is False, (prompt, validation.issues)
