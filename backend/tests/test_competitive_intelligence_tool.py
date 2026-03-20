from backend.app.core.tools import competitive_intelligence_tool as ct


def test_extract_product_query_handles_all_competitors_phrase() -> None:
    query = "faça uma pesquisa do produto fita 45x45 em todos os concorrentes"
    assert ct._extract_product_query(query) == "fita 45x45"


def test_extract_product_query_handles_market_research_phrase() -> None:
    query = "realize uma pesquisa de mercado do produto tnt branco"
    assert ct._extract_product_query(query) == "tnt branco"


def test_all_competitors_mode_is_detected() -> None:
    query = "pesquise fita 45x45 em todos os concorrentes"
    assert ct._all_competitors_requested(query) is True
    assert "amazon" in ct._default_scan_competitors(True)


def test_competitive_search_returns_success_when_all_providers_empty(monkeypatch) -> None:
    """Quando todos os providers retornam vazio, a tool deve retornar com status success e 0 itens."""
    monkeypatch.setattr(ct, "_search_mercadolivre", lambda *args, **kwargs: [])
    monkeypatch.setattr(ct, "_search_serpapi", lambda *args, **kwargs: [])
    monkeypatch.setattr(ct, "_search_competitor_playwright", lambda *args, **kwargs: [])
    monkeypatch.setattr(ct, "_search_competitor_crawler", lambda *args, **kwargs: [])
    monkeypatch.setattr(ct, "_search_competitor_web", lambda *args, **kwargs: [])
    monkeypatch.setattr(ct, "_search_social_competitor", lambda *args, **kwargs: [])
    monkeypatch.setattr(ct, "_search_bellart", lambda *args, **kwargs: [])
    monkeypatch.setattr(ct, "_load_manual_reference", lambda *args, **kwargs: [])

    tool_fn = getattr(ct.pesquisar_precos_concorrentes, "func", ct.pesquisar_precos_concorrentes)
    result = tool_fn(
        descricao_produto="faça uma pesquisa do produto fita 45x45 em todos os concorrentes",
        segmento="",
        estado="RJ",
        cidade="",
        limite="10",
        concorrentes="",
    )

    assert result["status"] == "success"
    assert isinstance(result["total_itens"], int)
    assert result["source"] == "tool.pesquisar_precos_concorrentes"
    assert isinstance(result.get("confidence"), float)
    assert isinstance(result.get("mode"), str)
    assert isinstance(result.get("citations"), list)


def test_build_competitor_search_queries_adds_variants_and_location() -> None:
    queries = ct._build_competitor_search_queries(
        product_query="fita adesiva 45x45",
        competitor="kalunga",
        domains=["kalunga.com.br"],
        estado="RJ",
        cidade="Rio de Janeiro",
    )

    assert queries
    assert any("site:kalunga.com.br" in q for q in queries)
    assert any("preço" in q for q in queries)
    assert any("Rio de Janeiro RJ" in q for q in queries)


def test_optimize_strategy_for_generic_query_prefers_fast_providers() -> None:
    priority, timeout, total_timeout, default_competitors = ct._optimize_strategy_for_query(
        priority=["playwright", "crawler", "websearch", "social", "mercadolivre", "serpapi", "bellart", "manual"],
        target_competitors=[],
        timeout=10,
        total_timeout=25,
        default_competitors=["americanas", "kalunga", "bellart"],
    )

    # websearch deve ser priorizado para queries genéricas
    assert priority[0] == "websearch"
    # timeout ajustado para busca rápida
    assert timeout <= 10
    # total_timeout ajustado
    assert total_timeout <= 35
    # competitors mantidos (lista <=6 não é cortada)
    assert len(default_competitors) <= 6


def test_generic_market_query_uses_fast_first_provider(monkeypatch) -> None:
    monkeypatch.setattr(ct.settings, "COMPETITIVE_PROVIDER_PRIORITY", "playwright,crawler,websearch,social,mercadolivre,serpapi,bellart,manual")
    monkeypatch.setattr(ct.settings, "COMPETITIVE_DOMAIN_WHITELIST", "kalunga.com.br,americanas.com.br")

    monkeypatch.setattr(ct, "_search_mercadolivre", lambda *args, **kwargs: [])
    monkeypatch.setattr(ct, "_search_serpapi", lambda *args, **kwargs: [])
    monkeypatch.setattr(ct, "_search_competitor_playwright", lambda *args, **kwargs: [])
    monkeypatch.setattr(ct, "_search_competitor_crawler", lambda *args, **kwargs: [])
    monkeypatch.setattr(
        ct,
        "_search_competitor_web",
        lambda *args, **kwargs: [
            {
                "concorrente": "kalunga",
                "produto": "TNT branco",
                "preco": 8.9,
                "moeda": "BRL",
                "fonte": "websearch_competitor",
                "url": "https://www.kalunga.com.br/prod/tnt-branco",
                "estado": "RJ",
                "cidade": "",
                "target_competitor": "kalunga",
            }
        ],
    )
    monkeypatch.setattr(ct, "_search_social_competitor", lambda *args, **kwargs: [])
    monkeypatch.setattr(ct, "_search_bellart", lambda *args, **kwargs: [])
    monkeypatch.setattr(ct, "_load_manual_reference", lambda *args, **kwargs: [])

    tool_fn = getattr(ct.pesquisar_precos_concorrentes, "func", ct.pesquisar_precos_concorrentes)
    result = tool_fn(
        descricao_produto="realize uma pesquisa de mercado do produto tnt branco",
        segmento="",
        estado="RJ",
        cidade="",
        limite="1",
        concorrentes="",
    )

    assert result["status"] == "success"
    assert result["total_itens"] == 1
    assert result["providers_used"]
    assert result["providers_used"][0] == "websearch"
    assert result["source"] == "tool.pesquisar_precos_concorrentes"
    assert isinstance(result.get("confidence"), float)
    assert isinstance(result.get("mode"), str)
    assert isinstance(result.get("citations"), list)


def test_diversify_competitor_results_limits_single_competitor_dominance() -> None:
    items = [
        {"concorrente": "Mercado Livre", "preco": 10 + i, "produto": f"ML {i}"}
        for i in range(8)
    ]
    items += [
        {"concorrente": "Kalunga", "preco": 9.5, "produto": "K 1"},
        {"concorrente": "Americanas", "preco": 9.8, "produto": "A 1"},
    ]
    items = sorted(items, key=lambda x: x["preco"])

    out = ct._diversify_competitor_results(items, limit=6, max_per_competitor=2)
    competitors = [str(x.get("concorrente")) for x in out]

    assert len(out) == 4
    assert competitors.count("Mercado Livre") <= 2
    assert "Kalunga" in competitors
    assert "Americanas" in competitors


def test_diversify_competitor_results_keeps_results_when_only_one_competitor() -> None:
    items = [
        {"concorrente": "Mercado Livre", "preco": 10 + i, "produto": f"ML {i}"}
        for i in range(5)
    ]
    out = ct._diversify_competitor_results(items, limit=5, max_per_competitor=2)

    assert len(out) == 5
    assert all(str(x.get("concorrente")) == "Mercado Livre" for x in out)


def test_market_web_collects_other_sources_even_when_ml_returns_many(monkeypatch) -> None:
    monkeypatch.setattr(
        ct,
        "_search_mercadolivre_market",
        lambda *_args, **_kwargs: [
            {
                "produto": f"Fita 45x45 ML item {i}",
                "preco": 10.0 + i,
                "moeda": "BRL",
                "vendedor": "Mercado Livre",
                "fonte": "mercadolivre",
                "url": f"https://produto.mercadolivre.com.br/MLB-{100+i}",
            }
            for i in range(8)
        ],
    )
    monkeypatch.setattr(
        ct,
        "_search_google_shopping_open",
        lambda *_args, **_kwargs: [
            {
                "produto": "Fita adesiva 45x45 Kalunga",
                "preco": 9.9,
                "moeda": "BRL",
                "vendedor": "",
                "fonte": "google_shopping",
                "url": "https://www.kalunga.com.br/prod/fita-adesiva",
            },
            {
                "produto": "Fita adesiva 45x45 Americanas",
                "preco": 9.7,
                "moeda": "BRL",
                "vendedor": "",
                "fonte": "google_shopping",
                "url": "https://www.americanas.com.br/prod/fita-adesiva",
            },
        ],
    )
    monkeypatch.setattr(ct, "_search_serpapi_open", lambda *_args, **_kwargs: [])
    monkeypatch.setattr(ct, "_search_duckduckgo_web", lambda *_args, **_kwargs: [])

    tool_fn = getattr(ct.pesquisar_mercado_web, "func", ct.pesquisar_mercado_web)
    result = tool_fn(termo_pesquisa="fita adesiva 45x45", limite="6")

    assert result["status"] == "success"
    assert "google_shopping" in result["providers_used"]
    competitors = {str(i.get("concorrente")) for i in result["itens"]}
    assert "Mercado Livre" in competitors
    assert "Kalunga" in competitors or "Americanas" in competitors
    assert result["source"] == "tool.pesquisar_mercado_web"
    assert isinstance(result.get("confidence"), float)
    assert isinstance(result.get("mode"), str)
    assert isinstance(result.get("citations"), list)


def test_market_web_infers_competitor_from_domain(monkeypatch) -> None:
    monkeypatch.setattr(ct, "_search_mercadolivre_market", lambda *_args, **_kwargs: [])
    monkeypatch.setattr(
        ct,
        "_search_google_shopping_open",
        lambda *_args, **_kwargs: [
            {
                "produto": "Cola Bastao 40g",
                "preco": 7.5,
                "moeda": "BRL",
                "vendedor": "",
                "fonte": "google_shopping",
                "url": "https://www.americanas.com.br/prod/cola-bastao",
            }
        ],
    )
    monkeypatch.setattr(ct, "_search_serpapi_open", lambda *_args, **_kwargs: [])
    monkeypatch.setattr(ct, "_search_duckduckgo_web", lambda *_args, **_kwargs: [])

    tool_fn = getattr(ct.pesquisar_mercado_web, "func", ct.pesquisar_mercado_web)
    result = tool_fn(termo_pesquisa="cola bastao 40g", limite="5")

    assert result["status"] == "success"
    assert result["itens"]
    assert result["itens"][0]["concorrente"] == "Americanas"
    assert "Americanas" in result.get("concorrentes_identificados", [])


def test_market_web_discards_irrelevant_items_for_nonexistent_product(monkeypatch) -> None:
    monkeypatch.setattr(
        ct,
        "_search_mercadolivre_market",
        lambda *_args, **_kwargs: [
            {
                "produto": "Cartão de visita 1000un",
                "preco": 80.0,
                "moeda": "BRL",
                "vendedor": "Mercado Livre",
                "fonte": "mercadolivre_api",
                "url": "https://produto.mercadolivre.com.br/MLB-999",
            }
        ],
    )
    monkeypatch.setattr(
        ct,
        "_search_google_shopping_open",
        lambda *_args, **_kwargs: [
            {
                "produto": "Livro O cavaleiro inexistente",
                "preco": 61.0,
                "moeda": "BRL",
                "vendedor": "Google Shopping",
                "fonte": "google_shopping",
                "url": "https://example.com/livro-inexistente",
            }
        ],
    )
    monkeypatch.setattr(ct, "_search_serpapi_open", lambda *_args, **_kwargs: [])
    monkeypatch.setattr(ct, "_search_duckduckgo_web", lambda *_args, **_kwargs: [])

    tool_fn = getattr(ct.pesquisar_mercado_web, "func", ct.pesquisar_mercado_web)
    result = tool_fn(termo_pesquisa="produto inexistente xyz-abc-999", limite="10")

    assert result["status"] == "success"
    assert result["total_itens"] == 0
    assert result["mode"] in {"deterministic_no_evidence", "deterministic_degraded_timeout"}


def test_market_web_expands_competitor_coverage_when_initially_concentrated(monkeypatch) -> None:
    monkeypatch.setattr(
        ct,
        "_search_mercadolivre_market",
        lambda *_args, **_kwargs: [
            {
                "produto": f"Fita 45x45 ML item {i}",
                "preco": 11.0 + i,
                "moeda": "BRL",
                "vendedor": "Mercado Livre",
                "fonte": "mercadolivre_api",
                "url": f"https://produto.mercadolivre.com.br/MLB-{300+i}",
            }
            for i in range(5)
        ],
    )
    monkeypatch.setattr(ct, "_search_google_shopping_open", lambda *_args, **_kwargs: [])
    monkeypatch.setattr(ct, "_search_serpapi_open", lambda *_args, **_kwargs: [])
    monkeypatch.setattr(ct, "_search_duckduckgo_web", lambda *_args, **_kwargs: [])

    def _fake_competitor_web(competitor: str, *_args, **_kwargs):
        if competitor == "kalunga":
            return [
                {
                    "concorrente": "kalunga",
                    "produto": "Fita Kalunga 45x45",
                    "preco": 12.0,
                    "moeda": "BRL",
                    "fonte": "websearch_competitor",
                    "url": "https://www.kalunga.com.br/prod/fita-45x45",
                }
            ]
        if competitor == "americanas":
            return [
                {
                    "concorrente": "americanas",
                    "produto": "Fita Americanas 45x45",
                    "preco": 12.9,
                    "moeda": "BRL",
                    "fonte": "websearch_competitor",
                    "url": "https://www.americanas.com.br/prod/fita-45x45",
                }
            ]
        return []

    monkeypatch.setattr(ct, "_search_competitor_web", _fake_competitor_web)

    tool_fn = getattr(ct.pesquisar_mercado_web, "func", ct.pesquisar_mercado_web)
    result = tool_fn(termo_pesquisa="fita 45x45", limite="6")

    assert result["status"] == "success"
    assert "competitor_web_fallback" in result["providers_used"]
    competitors = set(result.get("concorrentes_identificados", []))
    assert "Mercado Livre" in competitors
    assert "Kalunga" in competitors
    assert "Americanas" in competitors
    assert result.get("cobertura_concorrentes", {}).get("identificados", 0) >= 3


def test_market_web_mercadolivre_provider_prefers_api_and_increases_volume(monkeypatch) -> None:
    monkeypatch.setattr(
        ct,
        "_search_mercadolivre_market",
        lambda *_args, **_kwargs: [
            {
                "produto": f"Fita 45x45 ML API item {i}",
                "preco": 10.0 + i,
                "moeda": "BRL",
                "vendedor": "Mercado Livre",
                "fonte": "mercadolivre_api",
                "url": f"https://produto.mercadolivre.com.br/MLB-{200+i}",
            }
            for i in range(8)
        ],
    )
    monkeypatch.setattr(ct, "_search_google_shopping_open", lambda *_args, **_kwargs: [])
    monkeypatch.setattr(ct, "_search_serpapi_open", lambda *_args, **_kwargs: [])
    monkeypatch.setattr(ct, "_search_duckduckgo_web", lambda *_args, **_kwargs: [])

    tool_fn = getattr(ct.pesquisar_mercado_web, "func", ct.pesquisar_mercado_web)
    result = tool_fn(termo_pesquisa="fita 45x45", limite="6")

    assert result["status"] == "success"
    assert result["total_itens"] == 6
    assert "mercadolivre" in result["providers_used"]


def test_mercadolivre_market_provider_falls_back_to_html_when_api_empty(monkeypatch) -> None:
    monkeypatch.setattr(ct, "_search_mercadolivre", lambda *_args, **_kwargs: [])
    monkeypatch.setattr(
        ct,
        "_search_mercadolivre_open",
        lambda *_args, **_kwargs: [
            {
                "produto": "ML HTML item",
                "preco": 12.5,
                "moeda": "BRL",
                "vendedor": "Mercado Livre",
                "fonte": "mercadolivre",
                "url": "https://produto.mercadolivre.com.br/MLB-999",
            }
        ],
    )

    out = ct._search_mercadolivre_market("fita 45x45", limit=5, timeout=5)
    assert len(out) == 1
    assert out[0]["fonte"] == "mercadolivre"


def test_search_serpapi_open_uses_product_link_when_link_missing(monkeypatch) -> None:
    monkeypatch.setattr(ct.settings, "SERPAPI_API_KEY", "test-key")
    monkeypatch.setattr(
        ct,
        "_http_get_json",
        lambda *_args, **_kwargs: {
            "shopping_results": [
                {
                    "title": "Fita 45x45",
                    "extracted_price": 8.99,
                    "source": "Shopee",
                    "product_link": "https://www.google.com/search?ibp=oshop&q=fita+45x45",
                }
            ]
        },
    )

    out = ct._search_serpapi_open("fita 45x45", limit=5, timeout=5)
    assert len(out) == 1
    assert out[0]["url"].startswith("https://www.google.com/search?")


def test_search_serpapi_competitive_uses_product_link_when_link_missing(monkeypatch) -> None:
    monkeypatch.setattr(ct.settings, "SERPAPI_API_KEY", "test-key")
    monkeypatch.setattr(
        ct,
        "_http_get_json",
        lambda *_args, **_kwargs: {
            "shopping_results": [
                {
                    "title": "Fita 45x45",
                    "extracted_price": 8.99,
                    "source": "Kalunga",
                    "product_link": "https://www.google.com/search?ibp=oshop&q=fita+45x45",
                }
            ]
        },
    )

    out = ct._search_serpapi("fita 45x45", limit=5, timeout=5, estado="RJ", cidade="")
    assert len(out) == 1
    assert out[0]["url"].startswith("https://www.google.com/search?")
