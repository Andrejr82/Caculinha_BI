"""
Testes unitários para o endpoint de Learning
"""
import pytest
from fastapi.testclient import TestClient
from backend.app.infrastructure.database.models import User
from backend.app.api.v1.endpoints import learning as learning_endpoint


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


def test_get_unified_dataset_status_success(client: TestClient, test_admin_token: str, monkeypatch):
    monkeypatch.setattr(
        learning_endpoint,
        "get_unified_dataset_status",
        lambda rebuild_if_missing=False, base_dir=None: {
            "exists": True,
            "dataset_version": "v2.0.0",
            "records_total": 12,
            "completeness": {
                "runtime_ready": True,
                "production_ready": False,
                "missing_production_sources": ["feedback"],
            },
        },
    )

    response = client.get(
        "/api/v1/learning/unified-dataset-status",
        headers={"Authorization": f"Bearer {test_admin_token}"},
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["success"] is True
    assert payload["status"]["dataset_version"] == "v2.0.0"
    assert payload["status"]["completeness"]["runtime_ready"] is True


def test_get_unified_dataset_status_unauthorized(client: TestClient):
    response = client.get("/api/v1/learning/unified-dataset-status")
    assert response.status_code == 401
