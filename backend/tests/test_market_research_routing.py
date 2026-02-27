from backend.app.api.v1.endpoints.chat import (
    _should_use_market_web_fast_path,
    _should_bypass_cache_for_query,
)


def test_market_web_fast_path_only_for_explicit_mercado_livre() -> None:
    assert _should_use_market_web_fast_path("pesquisar preço no mercado livre de fita adesiva") is True


def test_market_web_fast_path_disabled_for_generic_market_research() -> None:
    assert _should_use_market_web_fast_path("faça uma pesquisa de mercado de fita adesiva 45x45") is False


def test_market_web_fast_path_disabled_when_other_competitors_mentioned() -> None:
    assert _should_use_market_web_fast_path("pesquisar no mercado livre e kalunga fita adesiva") is False


def test_market_web_fast_path_disabled_when_query_explicitly_mentions_competitors() -> None:
    assert _should_use_market_web_fast_path("pesquise fita 45x45 em todos os concorrentes") is False


def test_cache_is_bypassed_for_market_queries() -> None:
    assert _should_bypass_cache_for_query("faça uma pesquisa de mercado do produto fita 45x45") is True


def test_cache_is_not_bypassed_for_non_market_queries() -> None:
    assert _should_bypass_cache_for_query("qual o total de vendas ontem na une 1685") is False
