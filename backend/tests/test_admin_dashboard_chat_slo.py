from types import SimpleNamespace

import pytest

from backend.app.api.v1.endpoints.admin_dashboard import get_chat_slo_metrics
from backend.services.metrics import MetricsService


@pytest.fixture(autouse=True)
def reset_metrics():
    metrics = MetricsService()
    metrics.reset()
    yield
    metrics.reset()


@pytest.mark.asyncio
async def test_chat_slo_exposes_semantic_quality_percentages():
    metrics = MetricsService()
    metrics.increment("chat_requests_total", value=10)
    metrics.increment("chat_errors_total", value=1)
    metrics.increment("chat_cache_lookups_total", value=5)
    metrics.increment("chat_cache_hits_total", value=4)
    metrics.increment("chat_tool_calls_total", value=8)
    metrics.increment("chat_tokens_in_total", value=1200)
    metrics.increment("chat_tokens_out_total", value=800)
    metrics.set_gauge("tool_selection_accuracy", 0.8)
    metrics.set_gauge("citation_coverage", 0.6)
    metrics.set_gauge("no_data_false_positive_rate", 0.25)

    metrics.observe("chat_latency_seconds", 1.0)
    metrics.observe("chat_latency_seconds", 2.0, labels={"complexity": "simple"})
    metrics.observe("chat_latency_seconds", 4.0, labels={"complexity": "complex"})

    admin_user = SimpleNamespace(id="admin-1", role="admin", email="admin@agentbi.com")
    payload = await get_chat_slo_metrics(current_user=admin_user)

    assert payload.tool_selection_accuracy_pct == 80.0
    assert payload.citation_coverage_pct == 60.0
    assert payload.no_data_false_positive_pct == 25.0
