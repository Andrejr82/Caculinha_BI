"""
Testes unitários para o endpoint de Learning
"""
import pytest
from fastapi.testclient import TestClient
from app.infrastructure.database.models import User


def test_get_insights_success(client: TestClient, test_user_token: str):
    """
    Testa se o endpoint de insights retorna dados válidos
    """
    response = client.get(
        "/api/v1/learning/insights",
        headers={"Authorization": f"Bearer {test_user_token}"}
    )
    
    assert response.status_code == 200
    data = response.json()
    
    # Verificar estrutura da resposta
    assert "insights" in data
    assert isinstance(data["insights"], list)
    
    # Se houver insights, verificar estrutura
    if len(data["insights"]) > 0:
        insight = data["insights"][0]
        assert "type" in insight
        assert "title" in insight
        assert "description" in insight


def test_get_insights_unauthorized(client: TestClient):
    """
    Testa se o endpoint rejeita requisições sem autenticação
    """
    response = client.get("/api/v1/learning/insights")
    assert response.status_code == 401


def test_get_insights_types(client: TestClient, test_user_token: str):
    """
    Testa se os tipos de insights são válidos
    """
    response = client.get(
        "/api/v1/learning/insights",
        headers={"Authorization": f"Bearer {test_user_token}"}
    )
    
    assert response.status_code == 200
    data = response.json()
    
    valid_types = ["top_performer", "stock_alert"]
    
    for insight in data["insights"]:
        assert insight["type"] in valid_types


def test_get_insights_with_admin(client: TestClient, test_admin_token: str):
    """
    Testa se admin tem acesso aos insights
    """
    response = client.get(
        "/api/v1/learning/insights",
        headers={"Authorization": f"Bearer {test_admin_token}"}
    )
    
    assert response.status_code == 200
    data = response.json()
    assert "insights" in data
