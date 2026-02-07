"""
FASE 5 — Testes de Integração da API

Testes E2E dos endpoints da API v2 com dados reais.

Uso:
    pytest tests/test_fase5_api.py -v

Autor: Arquiteto de Sistema
Data: 2026-02-07
"""

import os
from pathlib import Path

import pytest
from httpx import AsyncClient, ASGITransport

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
    
    app = FastAPI(title="Caculinha BI Agent - Test")
    app.include_router(router, prefix="/api/v2")
    return app


@pytest.fixture
def client(app):
    """Cliente HTTP síncrono para testes."""
    from fastapi.testclient import TestClient
    return TestClient(app)


# =============================================================================
# TESTES — HEALTH ENDPOINTS
# =============================================================================

class TestHealthEndpoints:
    """Testes dos endpoints de health."""
    
    def test_health_check_basico(self, client):
        """Health check básico deve retornar 200."""
        response = client.get("/api/v2/health")
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "timestamp" in data
        print(f"\nHealth: {data}")
    
    def test_health_check_detalhado(self, client):
        """Health check detalhado deve retornar componentes."""
        response = client.get("/api/v2/health/detailed")
        
        assert response.status_code == 200
        data = response.json()
        assert "components" in data
        print(f"\nHealth Detalhado: {data}")


# =============================================================================
# TESTES — AGENTS ENDPOINTS
# =============================================================================

class TestAgentsEndpoints:
    """Testes dos endpoints de agentes."""
    
    def test_listar_agentes(self, client):
        """Deve listar todos os agentes."""
        response = client.get("/api/v2/agents")
        
        assert response.status_code == 200
        data = response.json()
        assert "agents" in data
        assert data["total"] >= 8
        print(f"\nAgentes: {[a['name'] for a in data['agents']]}")
    
    def test_detalhes_agente(self, client):
        """Deve retornar detalhes de um agente."""
        response = client.get("/api/v2/agents/SQLAgent")
        
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "SQLAgent"
        assert "capabilities" in data
        assert "tools" in data
        print(f"\nSQLAgent tools: {[t['name'] for t in data['tools']]}")
    
    def test_agente_nao_encontrado(self, client):
        """Deve retornar 404 para agente inexistente."""
        response = client.get("/api/v2/agents/AgenteInexistente")
        
        assert response.status_code == 404


# =============================================================================
# TESTES — CHAT ENDPOINTS
# =============================================================================

class TestChatEndpoints:
    """Testes dos endpoints de chat."""
    
    def test_chat_simples(self, client):
        """Deve processar uma mensagem de chat."""
        response = client.post(
            "/api/v2/chat",
            json={"message": "Qual o status do sistema?"},
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "content" in data
        assert "conversation_id" in data
        assert "agent_name" in data
        assert data["execution_time_ms"] > 0
        print(f"\nResposta do Chat:\n{data['content'][:300]}")
    
    def test_chat_com_tenant(self, client):
        """Deve respeitar o tenant_id do header."""
        response = client.post(
            "/api/v2/chat",
            json={"message": "Olá"},
            headers={"X-Tenant-ID": "lojas-cacula", "X-User-ID": "user-test"},
        )
        
        assert response.status_code == 200
    
    def test_chat_stream(self, client):
        """Deve retornar SSE stream."""
        response = client.post(
            "/api/v2/chat/stream",
            json={"message": "Olá"},
        )
        
        assert response.status_code == 200
        assert "text/event-stream" in response.headers.get("content-type", "")
    
    def test_historico_conversa(self, client):
        """Deve retornar histórico de conversa."""
        response = client.get("/api/v2/chat/history/conv-123")
        
        assert response.status_code == 200


# =============================================================================
# EXECUÇÃO DIRETA
# =============================================================================

if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s", "--tb=short"])
