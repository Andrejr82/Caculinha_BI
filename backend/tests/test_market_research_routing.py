from backend.app.api.v1.endpoints.chat import (
    _build_chat_cache_key,
    _should_use_market_web_fast_path,
    _should_bypass_cache_for_query,
    _resolve_competitive_market_followup_query,
)
from backend.app.config.settings import settings


def test_market_web_fast_path_enabled_for_explicit_mercado_livre() -> None:
    assert _should_use_market_web_fast_path("pesquisar preço no mercado livre de fita adesiva") is True


def test_market_web_fast_path_enabled_for_generic_market_research() -> None:
    assert _should_use_market_web_fast_path("faça uma pesquisa de mercado de fita adesiva 45x45") is True


def test_market_web_fast_path_disabled_when_other_competitors_mentioned() -> None:
    assert _should_use_market_web_fast_path("pesquisar no mercado livre e kalunga fita adesiva") is False


def test_market_web_fast_path_disabled_when_query_explicitly_mentions_competitors() -> None:
    assert _should_use_market_web_fast_path("pesquise fita 45x45 em todos os concorrentes") is False


def test_cache_is_bypassed_for_market_queries() -> None:
    assert _should_bypass_cache_for_query("faça uma pesquisa de mercado do produto fita 45x45") is True


def test_cache_is_not_bypassed_for_non_market_queries() -> None:
    assert _should_bypass_cache_for_query("qual o total de vendas ontem na une 1685") is False


def test_cache_is_bypassed_for_chart_queries_with_business_filters() -> None:
    assert _should_bypass_cache_for_query(
        "gere um gráfico com a venda do segmento tecidos em cada loja"
    ) is True


def test_cache_is_bypassed_for_table_queries_with_business_filters() -> None:
    assert _should_bypass_cache_for_query(
        "me mostre em tabela as vendas por loja do segmento papelaria"
    ) is True


def test_cache_is_bypassed_for_contextual_commercial_plan_followup() -> None:
    assert _should_bypass_cache_for_query("me dê um plano comercial para 7 dias com base nisso") is True


def test_cache_is_bypassed_for_short_contextual_followup() -> None:
    assert _should_bypass_cache_for_query("agora detalhe as próximas ações") is True


def test_cache_is_bypassed_for_last_response_followup() -> None:
    assert _should_bypass_cache_for_query("com base na última resposta, me dê um plano comercial") is True


def test_chat_cache_key_changes_when_parquet_changes(tmp_path, monkeypatch) -> None:
    parquet_file = tmp_path / "admmat.parquet"
    parquet_file.write_text("v1", encoding="utf-8")
    monkeypatch.setattr(settings, "PARQUET_DATA_PATH", str(parquet_file))

    key_before = _build_chat_cache_key("sessao-1", "vendas do segmento tecidos")

    parquet_file.write_text("versao-2-com-mais-dados", encoding="utf-8")
    key_after = _build_chat_cache_key("sessao-1", "vendas do segmento tecidos")

    assert key_before != key_after


def test_market_followup_query_reuses_previous_product_for_specific_competitor() -> None:
    chat_history = [
        {
            "role": "user",
            "content": "faça uma pesquisa de mercado do produto lapis de cor 12 cores",
            "metadata": {"context": {"market_product_hint": "lapis de cor 12 cores"}},
        },
        {
            "role": "assistant",
            "content": "## Resumo executivo\n- Pesquisa de mercado concluida para **lapis de cor 12 cores** com 15 referencias.",
            "metadata": {"context": {"source": "tool.pesquisar_mercado_web", "market_product_hint": "lapis de cor 12 cores"}},
        },
    ]

    resolved = _resolve_competitive_market_followup_query("e na Kalunga?", chat_history)

    assert "lapis de cor 12 cores" in resolved.lower()
    assert "kalunga" in resolved.lower()


def test_market_followup_query_reuses_previous_product_for_mercado_livre() -> None:
    chat_history = [
        {
            "role": "user",
            "content": "faça uma pesquisa de mercado do produto lapis de cor 12 cores",
            "metadata": {"context": {"market_product_hint": "lapis de cor 12 cores"}},
        },
        {
            "role": "assistant",
            "content": "## Resumo executivo\n- Pesquisa de mercado concluida para **lapis de cor 12 cores** com 15 referencias.",
            "metadata": {"context": {"source": "tool.pesquisar_mercado_web", "market_product_hint": "lapis de cor 12 cores"}},
        },
    ]

    resolved = _resolve_competitive_market_followup_query("e no Mercado Livre?", chat_history)

    assert resolved.lower() == "pesquisa de mercado de lapis de cor 12 cores no mercado livre"
