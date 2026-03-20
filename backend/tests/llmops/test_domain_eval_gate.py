from collections import defaultdict

from backend.app.services.chat_service_v3 import ChatServiceV3


DOMAIN_THRESHOLDS = {
    "data_query": 0.95,
    "dashboard": 0.95,
    "market_research": 0.85,
    "calculation": 0.95,
}


def _make_service() -> ChatServiceV3:
    # Avaliação de contrato: não precisa inicializar adapters/LLM.
    return ChatServiceV3.__new__(ChatServiceV3)


def _domain_check(domain: str, result: dict) -> bool:
    message = str(result.get("result", {}).get("mensagem", "") or "")
    internal_meta = result.get("_internal_meta", {}) if isinstance(result.get("_internal_meta"), dict) else {}

    if domain == "data_query":
        return "## Resumo executivo" in message and "## Tabela operacional" in message

    if domain == "dashboard":
        spec = result.get("dashboard_spec")
        return result.get("type") == "dashboard" and isinstance(spec, dict) and len(spec.get("widgets", [])) >= 1

    if domain == "market_research":
        source = str(result.get("source") or internal_meta.get("source") or "")
        citations = result.get("citations") if result.get("citations") not in (None, "", []) else internal_meta.get("citations")
        return source.startswith("tool.pesquisar_") and isinstance(citations, list) and len(citations) > 0

    if domain == "calculation":
        source = str(result.get("source") or internal_meta.get("source") or "")
        confidence = float(result.get("confidence") if result.get("confidence") is not None else (internal_meta.get("confidence") or 0.0))
        return source == "sandbox.code_gen_agent" and confidence >= 0.5 and bool(message.strip())

    return False


def test_domain_eval_gate_meets_minimum_thresholds():
    service = _make_service()
    cases = [
        {
            "domain": "data_query",
            "query": "analise vendas por segmento",
            "agent_response": {"response": "As vendas cresceram no periodo por segmento."},
        },
        {
            "domain": "dashboard",
            "query": "gere um dashboard do segmento ARTES",
            "agent_response": {
                "response": "Dashboard pronto.",
                "dashboard_spec": {
                    "title": "Dashboard ARTES",
                    "widgets": [{"kind": "kpi", "id": "vendas", "value": "1000"}],
                },
                "source": "tool.gerar_dashboard_executivo",
            },
        },
        {
            "domain": "market_research",
            "query": "faça pesquisa de mercado de caderno",
            "agent_response": {
                "response": "Pesquisa de mercado consolidada.",
                "source": "tool.pesquisar_mercado_web",
                "citations": [{"source": "example", "url": "https://example.com"}],
            },
        },
        {
            "domain": "calculation",
            "query": "calcule o eoq para demanda mensal",
            "agent_response": {
                "response": "Resultado calculado: EOQ de 120 unidades.",
                "source": "sandbox.code_gen_agent",
                "confidence": 0.91,
            },
        },
    ]

    totals = defaultdict(int)
    passes = defaultdict(int)

    for case in cases:
        domain = case["domain"]
        result = service._process_agent_response(
            case["agent_response"],
            query=case["query"],
            user_role="analyst",
        )
        totals[domain] += 1
        if _domain_check(domain, result):
            passes[domain] += 1

    domain_rates = {
        domain: (passes[domain] / totals[domain]) if totals[domain] > 0 else 0.0
        for domain in DOMAIN_THRESHOLDS
    }

    for domain, threshold in DOMAIN_THRESHOLDS.items():
        assert domain_rates[domain] >= threshold, (
            f"domain={domain} rate={domain_rates[domain]:.2%} threshold={threshold:.0%}"
        )
