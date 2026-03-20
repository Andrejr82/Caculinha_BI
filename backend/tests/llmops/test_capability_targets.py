from math import sqrt
from types import SimpleNamespace

import pytest

from backend.app.api.v1.endpoints.admin_dashboard import get_chat_slo_metrics
from backend.app.api.v1.endpoints.chat import _market_contract_from_payload
from backend.app.core.agents.code_gen_agent import CodeGenAgent
from backend.app.services.chat_service_v3 import ChatServiceV3
from backend.services.metrics import MetricsService


def _service() -> ChatServiceV3:
    # Evita inicializacao pesada para testes de contrato de saida.
    return ChatServiceV3.__new__(ChatServiceV3)


@pytest.fixture(autouse=True)
def _reset_metrics():
    metrics = MetricsService()
    metrics.reset()
    yield
    metrics.reset()


def test_bi_internal_capability_success_rate_target():
    service = _service()
    cases = []

    for i in range(12):
        cases.append(
            {
                "query": f"analise vendas por segmento no periodo {i}",
                "agent_response": {"response": "As vendas variaram por segmento no periodo analisado."},
                "expected": "data_query",
            }
        )

    for i in range(4):
        cases.append(
            {
                "query": f"gere dashboard interativo do segmento ARTES {i}",
                "agent_response": {
                    "response": "Dashboard gerado.",
                    "dashboard_spec": {
                        "title": f"Dashboard ARTES {i}",
                        "widgets": [{"kind": "kpi", "id": "vendas", "value": "1000"}],
                    },
                },
                "expected": "dashboard",
            }
        )

    for i in range(4):
        cases.append(
            {
                "query": f"gere grafico de vendas por loja {i}",
                "agent_response": {
                    "response": "Grafico pronto.",
                    "chart_data": {"type": "bar", "x": ["A", "B"], "y": [10, 20]},
                },
                "expected": "visualization",
            }
        )

    success = 0
    for case in cases:
        result = service._process_agent_response(case["agent_response"], query=case["query"], user_role="analyst")
        expected = case["expected"]
        if expected == "data_query":
            msg = str(result.get("result", {}).get("mensagem", ""))
            ok = "## Resumo executivo" in msg and "## Tabela operacional" in msg
        elif expected == "dashboard":
            ok = result.get("type") == "dashboard" and isinstance(result.get("dashboard_spec"), dict)
        else:
            ok = isinstance(result.get("chart_data"), dict) and bool(str(result.get("result", {}).get("mensagem", "")).strip())
        success += 1 if ok else 0

    rate = success / len(cases)
    assert rate >= 0.95


def test_market_research_evidence_coverage_target():
    payloads = []
    for i in range(9):
        payloads.append(
            {
                "source": "tool.pesquisar_mercado_web",
                "fontes_consultadas": [
                    {
                        "fonte": "site_publico",
                        "dominio": f"example{i}.com",
                        "url": f"https://example{i}.com/produto",
                        "concorrente": "concorrente_x",
                    }
                ],
            }
        )
    payloads.append({"source": "tool.pesquisar_mercado_web", "fontes_consultadas": []})

    covered = 0
    for payload in payloads:
        contract = _market_contract_from_payload(payload, default_source="tool.pesquisar_mercado_web")
        citations = contract.get("citations") or []
        if str(contract.get("source", "")).startswith("tool.") and len(citations) > 0:
            covered += 1

    coverage = covered / len(payloads)
    assert coverage >= 0.85


def test_calculation_concordance_target():
    agent = CodeGenAgent()
    scenarios = [
        (12000.0, 150.0, 0.15, 20.0),
        (15000.0, 110.0, 0.18, 25.0),
        (22000.0, 90.0, 0.12, 30.0),
        (18000.0, 130.0, 0.20, 18.0),
        (26000.0, 80.0, 0.10, 35.0),
    ]
    scenarios = scenarios * 4  # 20 cenarios

    hits = 0
    for demand_annual, order_cost, holding_cost_pct, unit_cost in scenarios:
        result = agent.calculate_eoq_internal(demand_annual, order_cost, holding_cost_pct, unit_cost)
        expected = round(sqrt((2.0 * demand_annual * order_cost) / (unit_cost * holding_cost_pct)), 0)
        actual = float(result.get("eoq", 0.0))
        if abs(actual - expected) <= 1.0:
            hits += 1

    concordance = hits / len(scenarios)
    assert concordance >= 0.95


@pytest.mark.asyncio
async def test_operational_reliability_target():
    metrics = MetricsService()
    metrics.increment("chat_requests_total", value=200)
    metrics.increment("chat_errors_total", value=1)

    for _ in range(30):
        metrics.observe("chat_latency_seconds", 2.5, labels={"complexity": "simple"})
        metrics.observe("chat_latency_seconds", 7.0, labels={"complexity": "complex"})
        metrics.observe("chat_latency_seconds", 5.0)

    admin_user = SimpleNamespace(id="admin-ops", role="admin", email="admin@agentbi.com")
    payload = await get_chat_slo_metrics(current_user=admin_user)

    assert payload.error_rate_pct < 1.0
    assert payload.p95_complex_ms <= 15000.0
    assert payload.slo_status == "healthy"
