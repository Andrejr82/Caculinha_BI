import json

from backend.app.core.agents.caculinha_bi_agent import CaculinhaBIAgent


def _bare_agent() -> CaculinhaBIAgent:
    return CaculinhaBIAgent.__new__(CaculinhaBIAgent)


def test_generate_structured_visual_narrative_renders_markdown_from_json_mode() -> None:
    agent = _bare_agent()
    agent._llm_generate_with_history = lambda *args, **kwargs: json.dumps(  # type: ignore[method-assign]
        {
            "headline": "Ruptura critica em papelaria",
            "summary": "As lojas com maior risco pedem reposicao imediata.",
            "key_findings": [
                "A UNE 1685 concentrou a maior perda potencial.",
                "O giro recente ficou acima da cobertura atual.",
            ],
            "recommended_actions": [
                "Priorizar reposicao ainda hoje.",
                "Revisar transferencia entre lojas vizinhas.",
            ],
        },
        ensure_ascii=False,
    )

    markdown = agent._generate_structured_visual_narrative(
        user_query="onde esta a maior ruptura?",
        task_type="inventory",
        fallback_text="Texto livre fallback",
        table_rows=[{"UNE": 1685, "RUPTURA": 12}],
    )

    assert "### Ruptura critica em papelaria" in markdown
    assert "**Principais achados**" in markdown
    assert "- A UNE 1685 concentrou a maior perda potencial." in markdown
    assert "**Ações recomendadas**" in markdown


def test_generate_structured_visual_narrative_falls_back_on_invalid_json() -> None:
    agent = _bare_agent()
    agent._llm_generate_with_history = lambda *args, **kwargs: "not-json"  # type: ignore[method-assign]

    markdown = agent._generate_structured_visual_narrative(
        user_query="mostre a tabela",
        task_type="analysis",
        fallback_text="Resumo fallback",
        table_rows=[{"SEGMENTO": "ARTES", "TOTAL_VENDAS": 1200}],
    )

    assert markdown == "Resumo fallback"
