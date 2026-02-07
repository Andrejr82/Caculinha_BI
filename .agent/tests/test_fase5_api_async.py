"""
FASE 5 — Testes Assíncronos da API

Testes E2E dos endpoints de chat usando httpx.AsyncClient
para suportar endpoints com lógica assíncrona interna.

Uso:
    pytest tests/test_fase5_api_async.py -v

Autor: Arquiteto de Sistema
Data: 2026-02-07
"""

import os
from pathlib import Path
import asyncio

import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport

# Configurar paths
import sys
BACKEND_DIR = Path(__file__).parent.parent.parent / "backend"
sys.path.insert(0, str(BACKEND_DIR))

from dotenv import load_dotenv
load_dotenv(BACKEND_DIR / ".env")


# =============================================================================
# CONFIGURAÇÃO PYTEST-ASYNCIO
# =============================================================================

# Forçar modo asyncio
pytest_plugins = ('pytest_asyncio',)


# =============================================================================
# FIXTURES
# =============================================================================

@pytest.fixture(scope="module")
def event_loop():
    """Cria event loop para os testes."""
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="module")
def app():
    """Cria app FastAPI para testes."""
    from fastapi import FastAPI
    from backend.api.v2 import router
    
    app = FastAPI(title="Caculinha BI Agent - Async Test")
    app.include_router(router, prefix="/api/v2")
    return app


@pytest_asyncio.fixture
async def async_client(app):
    """Cliente HTTP assíncrono para testes."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        yield client


# =============================================================================
# TESTES — CHAT ENDPOINTS (ASSÍNCRONOS)
# =============================================================================

class TestChatEndpointsAsync:
    """Testes assíncronos dos endpoints de chat."""
    
    @pytest.mark.asyncio
    async def test_chat_simples(self, async_client):
        """Deve processar uma mensagem de chat."""
        response = await async_client.post(
            "/api/v2/chat",
            json={"message": "Qual o status do sistema?"},
            timeout=60.0,
        )
        
        assert response.status_code == 200, f"Erro: {response.text}"
        data = response.json()
        assert "content" in data
        assert "conversation_id" in data
        assert "agent_name" in data
        assert data["execution_time_ms"] > 0
        print(f"\n✅ Chat Response:\n{data['content'][:500]}")
        print(f"   Agent: {data['agent_name']}")
        print(f"   Tempo: {data['execution_time_ms']:.2f}ms")
    
    @pytest.mark.asyncio
    async def test_chat_com_tenant(self, async_client):
        """Deve respeitar o tenant_id do header."""
        response = await async_client.post(
            "/api/v2/chat",
            json={"message": "Olá, tudo bem?"},
            headers={"X-Tenant-ID": "lojas-cacula", "X-User-ID": "user-test"},
            timeout=60.0,
        )
        
        assert response.status_code == 200, f"Erro: {response.text}"
        data = response.json()
        assert "content" in data
        print(f"\n✅ Chat com Tenant:\n{data['content'][:300]}")
    
    @pytest.mark.asyncio
    async def test_chat_query_dados(self, async_client):
        """Deve executar query SQL através do SQLAgent."""
        response = await async_client.post(
            "/api/v2/chat",
            json={"message": "Quantas tabelas existem no sistema?"},
            timeout=90.0,
        )
        
        assert response.status_code == 200, f"Erro: {response.text}"
        data = response.json()
        assert "content" in data
        print(f"\n✅ Query Response:\n{data['content'][:500]}")
    
    @pytest.mark.asyncio
    async def test_chat_stream(self, async_client):
        """Deve retornar SSE stream."""
        response = await async_client.post(
            "/api/v2/chat/stream",
            json={"message": "Olá"},
            timeout=60.0,
        )
        
        assert response.status_code == 200
        assert "text/event-stream" in response.headers.get("content-type", "")
        print(f"\n✅ Stream Response: Content-Type={response.headers.get('content-type')}")
    
    @pytest.mark.asyncio
    async def test_chat_insight(self, async_client):
        """Deve gerar insights sobre o sistema."""
        response = await async_client.post(
            "/api/v2/chat",
            json={"message": "Me dê um resumo do status do sistema"},
            timeout=90.0,
        )
        
        assert response.status_code == 200, f"Erro: {response.text}"
        data = response.json()
        assert "content" in data
        print(f"\n✅ Insight Response:\n{data['content'][:500]}")


# =============================================================================
# TESTES — INTEGRAÇÃO COMPLETA
# =============================================================================

class TestIntegracaoCompleta:
    """Testes de integração end-to-end."""
    
    @pytest.mark.asyncio
    async def test_fluxo_completo(self, async_client):
        """Testa fluxo completo: health → agents → chat."""
        # 1. Health check
        health = await async_client.get("/api/v2/health")
        assert health.status_code == 200
        print("\n✅ 1. Health check OK")
        
        # 2. Listar agentes
        agents = await async_client.get("/api/v2/agents")
        assert agents.status_code == 200
        agent_list = agents.json()
        print(f"✅ 2. Agentes: {[a['name'] for a in agent_list['agents']]}")
        
        # 3. Enviar mensagem de chat
        chat = await async_client.post(
            "/api/v2/chat",
            json={"message": "Olá, estou testando o sistema"},
            timeout=60.0,
        )
        assert chat.status_code == 200
        chat_data = chat.json()
        print(f"✅ 3. Chat respondeu: {chat_data['agent_name']}")
        
        print("\n🎉 Fluxo completo funcionando!")


# =============================================================================
# EXECUÇÃO DIRETA
# =============================================================================

if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s", "--tb=short"])
