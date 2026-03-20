from __future__ import annotations

from types import SimpleNamespace

import pytest
from fastapi.testclient import TestClient

from backend.main import app
from backend.app.api.dependencies import get_current_active_user


@pytest.fixture(scope="module")
def client():
    return TestClient(app)


@pytest.fixture(autouse=True)
def override_current_user():
    async def _override_user():
        return SimpleNamespace(
            id="test-user-id",
            username="test-user",
            email="test@example.com",
            role="admin",
            is_active=True,
            allowed_segments='["*"]',
        )

    app.dependency_overrides[get_current_active_user] = _override_user
    try:
        yield
    finally:
        app.dependency_overrides.pop(get_current_active_user, None)


def test_suppliers_metrics(client: TestClient):
    response = client.get("/api/v1/dashboard/suppliers/metrics")
    assert response.status_code == 200

    data = response.json()
    assert "suppliers" in data
    assert isinstance(data["suppliers"], list)

    if data["suppliers"]:
        sample = data["suppliers"][0]
        assert "nome" in sample
        assert "taxa_ruptura" in sample


def test_forecast_tool(client: TestClient):
    payload = {
        "produto_id": "59294",
        "periodo_dias": 30,
        "considerar_sazonalidade": True,
    }
    response = client.post("/api/v1/dashboard/tools/prever_demanda", json=payload)
    assert response.status_code == 200

    data = response.json()
    if "error" in data:
        assert "produto" in data
    else:
        assert "forecast" in data
        assert "forecast_ajustado" in data


def test_eoq_tool(client: TestClient):
    payload = {"produto_id": "59294"}
    response = client.post("/api/v1/dashboard/tools/calcular_eoq", json=payload)
    assert response.status_code == 200

    data = response.json()
    if "error" in data:
        assert "produto" in data
    else:
        assert "eoq" in data
