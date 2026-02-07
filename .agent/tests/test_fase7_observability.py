"""
FASE 7 — Testes de Observabilidade e Billing

Testes para MetricsService, BillingService e endpoints de métricas.

Uso:
    pytest tests/test_fase7_observability.py -v

Autor: Arquiteto de Sistema
Data: 2026-02-07
"""

import os
from pathlib import Path
import time

import pytest
from fastapi.testclient import TestClient

# Configurar paths
import sys
BACKEND_DIR = Path(__file__).parent.parent.parent / "backend"
sys.path.insert(0, str(BACKEND_DIR))

from dotenv import load_dotenv
load_dotenv(BACKEND_DIR / ".env")


# =============================================================================
# FIXTURES
# =============================================================================

@pytest.fixture
def app():
    """Cria app FastAPI para testes."""
    from fastapi import FastAPI
    from backend.api.v2 import router
    
    app = FastAPI(title="Caculinha BI Agent - Observability Test")
    app.include_router(router, prefix="/api/v2")
    return app


@pytest.fixture
def client(app):
    """Cliente HTTP para testes."""
    return TestClient(app)


# =============================================================================
# TESTES — METRICS SERVICE
# =============================================================================

class TestMetricsService:
    """Testes do serviço de métricas."""
    
    def test_singleton(self):
        """MetricsService deve ser singleton."""
        from backend.services.metrics import MetricsService
        
        m1 = MetricsService()
        m2 = MetricsService()
        
        assert m1 is m2
        print("\n✅ MetricsService é singleton")
    
    def test_counter(self):
        """Counter deve incrementar corretamente."""
        from backend.services.metrics import MetricsService
        
        metrics = MetricsService()
        metrics.reset()
        
        metrics.increment("test_counter")
        metrics.increment("test_counter")
        metrics.increment("test_counter", 5)
        
        assert metrics.get_counter("test_counter") == 7
        print("\n✅ Counter: 7")
    
    def test_gauge(self):
        """Gauge deve armazenar valor."""
        from backend.services.metrics import MetricsService
        
        metrics = MetricsService()
        metrics.set_gauge("test_gauge", 42.5)
        
        assert metrics.get_gauge("test_gauge") == 42.5
        print("\n✅ Gauge: 42.5")
    
    def test_histogram(self):
        """Histogram deve calcular estatísticas."""
        from backend.services.metrics import MetricsService
        
        metrics = MetricsService()
        metrics.reset()
        
        for i in range(100):
            metrics.observe("test_latency", i / 100)
        
        stats = metrics.get_histogram_stats("test_latency")
        
        assert stats["count"] == 100
        assert stats["min"] == 0
        assert stats["max"] == 0.99
        assert "p50" in stats
        print(f"\n✅ Histogram stats: count={stats['count']}, avg={stats['avg']:.2f}")
    
    def test_timer_context(self):
        """Timer context manager deve medir tempo."""
        from backend.services.metrics import MetricsService
        
        metrics = MetricsService()
        metrics.reset()
        
        with metrics.timer("test_operation"):
            time.sleep(0.1)
        
        stats = metrics.get_histogram_stats("test_operation")
        
        assert stats["count"] == 1
        assert stats["avg"] >= 0.1
        print(f"\n✅ Timer: {stats['avg']:.3f}s")
    
    def test_labels(self):
        """Métricas com labels devem ser separadas."""
        from backend.services.metrics import MetricsService
        
        metrics = MetricsService()
        metrics.reset()
        
        metrics.increment("requests", labels={"tenant": "A"})
        metrics.increment("requests", labels={"tenant": "B"})
        metrics.increment("requests", labels={"tenant": "A"})
        
        assert metrics.get_counter("requests", labels={"tenant": "A"}) == 2
        assert metrics.get_counter("requests", labels={"tenant": "B"}) == 1
        print("\n✅ Labels funcionando")


# =============================================================================
# TESTES — BILLING SERVICE
# =============================================================================

class TestBillingService:
    """Testes do serviço de billing."""
    
    def test_singleton(self):
        """BillingService deve ser singleton."""
        from backend.services.billing import BillingService
        
        b1 = BillingService()
        b2 = BillingService()
        
        assert b1 is b2
        print("\n✅ BillingService é singleton")
    
    def test_record_usage(self):
        """Deve registrar uso corretamente."""
        from backend.services.billing import BillingService, UsageType
        
        billing = BillingService()
        billing.reset_usage("test-tenant")
        
        billing.record_usage("test-tenant", UsageType.API_CALLS, 10)
        billing.record_usage("test-tenant", UsageType.TOKENS, 1000)
        
        usage = billing.get_usage("test-tenant")
        
        assert usage["api_calls"] == 10
        assert usage["tokens"] == 1000
        print(f"\n✅ Usage: {usage}")
    
    def test_plans(self):
        """Planos devem estar configurados."""
        from backend.services.billing import BillingService, BillingPlan
        
        billing = BillingService()
        
        billing.set_plan("test-tenant", BillingPlan.PRO)
        
        assert billing.get_plan("test-tenant") == BillingPlan.PRO
        print("\n✅ Plano PRO configurado")
    
    def test_calculate_cost(self):
        """Deve calcular custo corretamente."""
        from backend.services.billing import BillingService, BillingPlan, UsageType
        
        billing = BillingService()
        billing.reset_usage("cost-test")
        billing.set_plan("cost-test", BillingPlan.PRO)
        
        billing.record_usage("cost-test", UsageType.API_CALLS, 100)
        billing.record_usage("cost-test", UsageType.TOKENS, 10000)
        
        cost = billing.calculate_cost("cost-test")
        
        assert cost["total_brl"] >= 0
        assert "breakdown" in cost
        print(f"\n✅ Custo calculado: R$ {cost['total_brl']}")
    
    def test_generate_invoice(self):
        """Deve gerar fatura."""
        from backend.services.billing import BillingService
        
        billing = BillingService()
        
        invoice = billing.generate_invoice("invoice-test")
        
        assert "invoice_id" in invoice
        assert invoice["status"] == "pending"
        print(f"\n✅ Fatura gerada: {invoice['invoice_id']}")


# =============================================================================
# TESTES — METRICS ENDPOINT
# =============================================================================

class TestMetricsEndpoint:
    """Testes dos endpoints de métricas."""
    
    def test_get_metrics(self, client):
        """Endpoint /metrics deve retornar métricas."""
        response = client.get("/api/v2/metrics")
        
        assert response.status_code == 200
        data = response.json()
        assert "uptime_seconds" in data
        assert "counters" in data
        print(f"\n✅ Métricas: uptime={data['uptime_seconds']:.2f}s")
    
    def test_get_usage(self, client):
        """Endpoint /metrics/usage deve retornar uso."""
        response = client.get("/api/v2/metrics/usage")
        
        assert response.status_code == 200
        data = response.json()
        assert "tenant_id" in data
        assert "plan" in data
        print(f"\n✅ Usage: tenant={data['tenant_id']}, plan={data['plan']}")
    
    def test_get_invoice(self, client):
        """Endpoint /metrics/invoice deve gerar fatura."""
        response = client.get("/api/v2/metrics/invoice")
        
        assert response.status_code == 200
        data = response.json()
        assert "invoice_id" in data
        print(f"\n✅ Invoice: {data['invoice_id']}")


# =============================================================================
# TESTES — LOGGING
# =============================================================================

class TestLoggingConfig:
    """Testes da configuração de logging."""
    
    def test_setup_logging(self):
        """Deve configurar logging sem erros."""
        from backend.services.logging_config import setup_logging, get_logger
        
        setup_logging(log_level="INFO", json_format=False)
        
        logger = get_logger("test")
        assert logger is not None
        logger.info("test_message", key="value")
        
        print("\n✅ Logging configurado")
    
    def test_bind_context(self):
        """Deve vincular contexto ao log."""
        from backend.services.logging_config import bind_request_context, clear_request_context
        
        bind_request_context(
            request_id="req-123",
            tenant_id="test-tenant",
            user_id="user-456"
        )
        
        # Contexto vinculado
        clear_request_context()
        
        print("\n✅ Contexto vinculado e limpo")


# =============================================================================
# EXECUÇÃO DIRETA
# =============================================================================

if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s", "--tb=short"])
