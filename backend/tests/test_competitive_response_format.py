from backend.app.core.agents.caculinha_bi_agent import CaculinhaBIAgent


def test_competitive_response_hides_internal_system_fields() -> None:
    agent = CaculinhaBIAgent.__new__(CaculinhaBIAgent)
    tool_result = {
        "itens": [
            {
                "concorrente": "benchmark_mercado",
                "produto": "Fita adesiva 45x45",
                "preco": 10.49,
                "fonte": "benchmark_seed_local",
                "url": "",
            }
        ],
        "total_itens": 1,
        "preco_medio_referencia": 10.49,
        "fallback_benchmark_aplicado": True,
        "metodo_consulta": "fallback_seed_local",
        "quality_gate": {"validated": 0, "discarded": 0},
        "escopo": {"estado": "RJ", "cidade": "", "segmento": ""},
        "fontes_consultadas": [
            {"concorrente": "benchmark_mercado", "fonte": "benchmark_seed_local", "dominio": "manual", "url": ""}
        ],
    }

    out = agent._format_deterministic_result(
        user_query="pesquise preço de fita 45x45",
        tool_name="pesquisar_precos_concorrentes",
        tool_result=tool_result,
    )
    msg = out["result"]["mensagem"]

    assert "## Resumo executivo" in msg
    assert "## Tabela operacional" in msg
    assert "## Ação recomendada" in msg
    assert "## Recorte e evidência" in msg
    assert "## Fontes" in msg
    assert "## Como melhorar a próxima pesquisa" in msg
    assert "Quality Gate" not in msg
    assert "fallback_seed_local" not in msg
    assert "metodo_consulta" not in msg
    assert "Referência de mercado" in msg
