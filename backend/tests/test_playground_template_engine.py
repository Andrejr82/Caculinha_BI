from backend.app.core.playground_template_engine import resolve_playground_template, load_bi_templates_catalog


def test_template_catalog_loads():
    catalog = load_bi_templates_catalog()
    assert catalog.get("version")
    assert len(catalog.get("templates", [])) >= 3


def test_template_matches_margin_prompt():
    result = resolve_playground_template("Preciso analisar margem por categoria das lojas.", json_mode=False)
    assert result is not None
    assert result.intent == "bi.margem_categoria"
    assert "## Resumo" in result.response


def test_template_returns_none_when_not_matched():
    result = resolve_playground_template("Qual a previsão do tempo amanhã?", json_mode=True)
    assert result is None
