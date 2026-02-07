"""
FASE 6 — Testes de SaaS (Auth, Multi-tenancy, Rate Limit)

Testes de integração para middlewares e endpoints de autenticação.

Uso:
    pytest tests/test_fase6_saas.py -v

Autor: Arquiteto de Sistema
Data: 2026-02-07
"""

import os
from pathlib import Path

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
    
    app = FastAPI(title="Caculinha BI Agent - SaaS Test")
    app.include_router(router, prefix="/api/v2")
    return app


@pytest.fixture
def client(app):
    """Cliente HTTP para testes."""
    return TestClient(app)


# =============================================================================
# TESTES — AUTH ENDPOINTS
# =============================================================================

class TestAuthEndpoints:
    """Testes dos endpoints de autenticação."""
    
    def test_login_sucesso(self, client):
        """Login com credenciais válidas deve retornar token."""
        response = client.post(
            "/api/v2/auth/login",
            json={
                "email": "admin@lojas-cacula.com.br",
                "password": "admin123",
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"
        assert data["role"] == "admin"
        print(f"\n✅ Login: Token gerado para {data['user_id']}")
    
    def test_login_credenciais_invalidas(self, client):
        """Login com credenciais inválidas deve retornar 401."""
        response = client.post(
            "/api/v2/auth/login",
            json={
                "email": "invalid@test.com",
                "password": "wrong",
            }
        )
        
        assert response.status_code == 401
        print("\n✅ Login inválido retornou 401")
    
    def test_me_com_token(self, client):
        """Endpoint /me com token válido deve retornar perfil."""
        # Login primeiro
        login = client.post(
            "/api/v2/auth/login",
            json={
                "email": "test@test.com",
                "password": "test123",
            }
        )
        token = login.json()["access_token"]
        
        # Chamar /me
        response = client.get(
            "/api/v2/auth/me",
            headers={"Authorization": f"Bearer {token}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["user_id"] == "user-test"
        print(f"\n✅ Perfil: {data['name']}")
    
    def test_me_sem_token(self, client):
        """Endpoint /me sem token deve retornar 401."""
        response = client.get("/api/v2/auth/me")
        
        assert response.status_code == 401
    
    def test_refresh_token(self, client):
        """Refresh token deve retornar novo token."""
        # Login primeiro
        login = client.post(
            "/api/v2/auth/login",
            json={
                "email": "test@test.com",
                "password": "test123",
            }
        )
        token = login.json()["access_token"]
        
        # Refresh
        response = client.post(
            "/api/v2/auth/refresh",
            json={"refresh_token": token}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        print("\n✅ Token renovado com sucesso")
    
    def test_logout(self, client):
        """Logout deve retornar sucesso."""
        response = client.post("/api/v2/auth/logout")
        
        assert response.status_code == 200


# =============================================================================
# TESTES — JWT FUNCTIONS
# =============================================================================

class TestJWTFunctions:
    """Testes das funções de JWT."""
    
    def test_create_and_decode_token(self):
        """Criar e decodificar token deve funcionar."""
        from backend.api.middleware.auth import create_access_token, decode_token
        
        # Criar token
        token = create_access_token(
            user_id="test-user",
            tenant_id="test-tenant",
            role="admin"
        )
        
        assert token is not None
        assert len(token) > 50
        
        # Decodificar
        payload = decode_token(token)
        
        assert payload["user_id"] == "test-user"
        assert payload["tenant_id"] == "test-tenant"
        assert payload["role"] == "admin"
        print(f"\n✅ Token criado e decodificado: {len(token)} chars")


# =============================================================================
# TESTES — TENANT MIDDLEWARE
# =============================================================================

class TestTenantMiddleware:
    """Testes do middleware de tenant."""
    
    def test_tenant_plans(self):
        """Planos de tenant devem estar configurados."""
        from backend.api.middleware.tenant import TENANT_PLANS
        
        assert "free" in TENANT_PLANS
        assert "pro" in TENANT_PLANS
        assert "enterprise" in TENANT_PLANS
        
        # Enterprise deve ter mais recursos
        assert TENANT_PLANS["enterprise"]["max_requests_per_hour"] > TENANT_PLANS["free"]["max_requests_per_hour"]
        print(f"\n✅ Planos: {list(TENANT_PLANS.keys())}")
    
    def test_tenant_config(self):
        """Configuração de tenant deve ser resolvida."""
        from backend.api.middleware.tenant import get_tenant_limits
        
        limits = get_tenant_limits("lojas-cacula")
        
        assert "max_requests_per_hour" in limits or limits == {}
        print(f"\n✅ Limites obtidos")


# =============================================================================
# TESTES — RATE LIMIT
# =============================================================================

class TestRateLimitMiddleware:
    """Testes do middleware de rate limit."""
    
    def test_rate_limit_status(self):
        """Status de rate limit deve funcionar."""
        from backend.api.middleware.rate_limit import get_rate_limit_status, reset_rate_limit
        
        # Resetar limites
        reset_rate_limit("test-tenant", "test-user")
        
        # Verificar status
        status = get_rate_limit_status("test-tenant", "test-user")
        
        assert status["requests_in_window"] == 0
        print(f"\n✅ Rate limit status: {status}")


# =============================================================================
# TESTES — FLUXO COMPLETO COM AUTH
# =============================================================================

class TestFluxoComAuth:
    """Testes de fluxo completo com autenticação."""
    
    def test_chat_com_token(self, client):
        """Chat com token de autenticação."""
        # Login
        login = client.post(
            "/api/v2/auth/login",
            json={
                "email": "admin@lojas-cacula.com.br",
                "password": "admin123",
            }
        )
        token = login.json()["access_token"]
        
        # Chat com token
        response = client.post(
            "/api/v2/chat",
            json={"message": "Olá, estou autenticado"},
            headers={
                "Authorization": f"Bearer {token}",
                "X-Tenant-ID": "lojas-cacula",
            }
        )
        
        assert response.status_code == 200
        print(f"\n✅ Chat autenticado funcionando")


# =============================================================================
# EXECUÇÃO DIRETA
# =============================================================================

if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s", "--tb=short"])
