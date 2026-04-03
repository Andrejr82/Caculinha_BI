import pytest
import time

from backend.app.api.v1.endpoints import chat as chat_endpoint


def test_market_research_message_lists_competitors(monkeypatch) -> None:
    monkeypatch.setattr(chat_endpoint, "_lookup_internal_price", lambda *_args, **_kwargs: {})

    payload = {
        "status": "success",
        "itens": [
            {
                "concorrente": "Kalunga",
                "produto": "Fita adesiva 45x45",
                "preco": 10.5,
                "fonte": "websearch_competitor",
                "url": "https://www.kalunga.com.br/prod/fita",
            },
            {
                "concorrente": "Americanas",
                "produto": "Fita adesiva 45x45",
                "preco": 11.2,
                "fonte": "websearch_competitor",
                "url": "https://www.americanas.com.br/prod/fita",
            },
        ],
    }

    msg = chat_endpoint._build_competitive_structured_business_message(
        query="pesquisa de mercado fita adesiva 45x45",
        payload=payload,
    )

    assert "Concorrentes com preço identificado:" in msg
    assert "Kalunga" in msg
    assert "Americanas" in msg


def test_market_research_message_warns_when_single_competitor(monkeypatch) -> None:
    monkeypatch.setattr(chat_endpoint, "_lookup_internal_price", lambda *_args, **_kwargs: {})

    payload = {
        "status": "success",
        "itens": [
            {
                "concorrente": "Mercado Livre",
                "produto": "Fita adesiva 45x45",
                "preco": 10.5,
                "fonte": "mercadolivre_api",
                "url": "https://produto.mercadolivre.com.br/MLB-123",
            }
        ],
    }

    msg = chat_endpoint._build_competitive_structured_business_message(
        query="pesquisa de mercado fita adesiva 45x45",
        payload=payload,
    )

    assert "Cobertura concentrada em Mercado Livre" in msg


def test_business_source_label_prefers_competitor_for_serpapi_sources() -> None:
    label = chat_endpoint._business_source_label(
        {
            "fonte": "serpapi_shopping",
            "concorrente": "Shopee",
            "url": "https://www.google.com/search?ibp=oshop&q=fita+45x45",
        }
    )
    assert label == "Shopee"


@pytest.mark.asyncio
async def test_competitive_fast_path_falls_back_to_market_web_when_no_public_evidence(monkeypatch) -> None:
    async def _fake_market_web(_query: str) -> str:
        return "fallback market web ok"

    monkeypatch.setattr(chat_endpoint, "_run_market_research_fast_path", _fake_market_web)
    monkeypatch.setattr(chat_endpoint, "_has_specific_competitor", lambda _q: False)

    def _fake_competitive_tool(**_kwargs):
        return {"status": "success", "itens": []}

    monkeypatch.setattr(chat_endpoint, "pesquisar_precos_concorrentes", _fake_competitive_tool)

    out = await chat_endpoint._run_competitive_market_fast_path(
        "faça uma pesquisa de mercado do produto fita 45x45"
    )
    assert out == "fallback market web ok"


@pytest.mark.asyncio
async def test_competitive_fast_path_falls_back_to_market_web_on_timeout(monkeypatch) -> None:
    async def _fake_market_web(_query: str) -> str:
        return "fallback market web timeout ok"

    monkeypatch.setattr(chat_endpoint, "_run_market_research_fast_path", _fake_market_web)
    monkeypatch.setattr(chat_endpoint, "_has_specific_competitor", lambda _q: False)
    monkeypatch.setattr(chat_endpoint, "_market_fast_path_timeout_seconds", lambda: 0.01)

    def _slow_competitive_tool(**_kwargs):
        time.sleep(0.05)
        return {"status": "success", "itens": []}

    monkeypatch.setattr(chat_endpoint, "pesquisar_precos_concorrentes", _slow_competitive_tool)

    out = await chat_endpoint._run_competitive_market_fast_path(
        "faça uma pesquisa de mercado do produto caneta bic"
    )
    assert out == "fallback market web timeout ok"


@pytest.mark.asyncio
async def test_market_fast_path_payload_exposes_contract_fields(monkeypatch) -> None:
    def _fake_market_tool(**_kwargs):
        return {
            "status": "success",
            "itens": [
                {
                    "concorrente": "Kalunga",
                    "produto": "Fita adesiva 45x45",
                    "preco": 10.5,
                    "fonte": "websearch_competitor",
                    "url": "https://www.kalunga.com.br/prod/fita",
                }
            ],
            "source": "tool.pesquisar_mercado_web",
            "confidence": 0.78,
            "mode": "deterministic_tool",
            "citations": [
                {
                    "source": "websearch_competitor",
                    "domain": "kalunga.com.br",
                    "url": "https://www.kalunga.com.br/prod/fita",
                    "competitor": "Kalunga",
                }
            ],
        }

    monkeypatch.setattr(chat_endpoint, "pesquisar_mercado_web", _fake_market_tool)

    out = await chat_endpoint._run_market_research_fast_path(
        "pesquisa de mercado fita adesiva 45x45",
        return_payload=True,
    )

    assert isinstance(out, dict)
    assert isinstance(out.get("text"), str)
    payload = out.get("payload", {})
    assert payload.get("source") == "tool.pesquisar_mercado_web"
    assert isinstance(payload.get("confidence"), float)
    assert isinstance(payload.get("mode"), str)
    assert isinstance(payload.get("citations"), list)


@pytest.mark.asyncio
async def test_market_fast_path_payload_marks_timeout_mode(monkeypatch) -> None:
    monkeypatch.setattr(chat_endpoint, "_market_fast_path_timeout_seconds", lambda: 0.01)

    def _slow_market_tool(**_kwargs):
        time.sleep(0.05)
        return {"status": "success", "itens": []}

    monkeypatch.setattr(chat_endpoint, "pesquisar_mercado_web", _slow_market_tool)

    out = await chat_endpoint._run_market_research_fast_path(
        "pesquisa de mercado fita adesiva 45x45",
        return_payload=True,
    )

    payload = out.get("payload", {}) if isinstance(out, dict) else {}
    assert payload.get("source") == "tool.pesquisar_mercado_web"
    assert payload.get("mode") == "deterministic_degraded_timeout"
