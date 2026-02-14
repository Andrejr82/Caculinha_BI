from backend.app.core.playground_rules_engine import resolve_playground_rule, load_bi_intents_catalog


def test_rule_matches_parquet_status_error():
    result = resolve_playground_rule(
        message="Crie um script para ler um arquivo Parquet e filtrar linhas onde status é error.",
        json_mode=False,
    )
    assert result is not None
    assert result.matched is True
    assert result.intent == "parquet.filter.status_error"
    assert "polars" in result.response.lower()


def test_rule_matches_sql_products_no_sales():
    result = resolve_playground_rule(
        message="Escreva uma query SQL para encontrar produtos que não venderam nos últimos 6 meses.",
        json_mode=True,
    )
    assert result is not None
    assert result.matched is True
    assert result.intent == "sql.produtos_sem_venda_6_meses"
    assert "sqlserver" in result.response.lower()


def test_rule_returns_none_for_non_catalog_prompt():
    result = resolve_playground_rule(
        message="Explique o conceito de margem de contribuição com exemplos.",
        json_mode=False,
    )
    assert result is None


def test_rule_matches_ruptura_store_period():
    result = resolve_playground_rule(
        message="Monte uma SQL de ruptura por loja e período para o time de BI.",
        json_mode=False,
    )
    assert result is not None
    assert result.intent == "sql.ruptura_por_loja_periodo"
    assert "@loja" in result.response


def test_rule_matches_transfer_suggestions():
    result = resolve_playground_rule(
        message="Preciso de uma query de transferências entre lojas com base no estoque.",
        json_mode=True,
    )
    assert result is not None
    assert result.intent == "sql.sugestao_transferencia_lojas"
    assert "qtd_sugerida" in result.response


def test_rule_matches_admat_une():
    result = resolve_playground_rule(
        message="Crie um checklist ADMAT UNE com média comum e linha verde.",
        json_mode=True,
    )
    assert result is not None
    assert result.intent == "bi.admat_une_checklist"
    assert "regras_chave" in result.response


def test_catalog_loads_with_intents():
    catalog = load_bi_intents_catalog()
    assert catalog.get("version")
    assert len(catalog.get("intents", [])) >= 5
