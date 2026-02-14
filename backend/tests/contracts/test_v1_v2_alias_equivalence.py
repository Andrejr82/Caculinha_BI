import pytest
from fastapi.testclient import TestClient
from backend.main import app

client = TestClient(app)

@pytest.mark.parametrize("path", [
    "health",
    "auth/login", # We'll check 405 or 422 if we don't send data
    "dashboard/metrics/executive-kpis",
    "rupturas/summary",
    "transfers/suggestions",
    "analytics/kpis",
])
def test_v1_v2_equivalence_exists(path):
    """Verifica se os endpoints existem em ambas as versões e não retornam 404."""
    response_v1 = client.get(f"/api/v1/{path}")
    response_v2 = client.get(f"/api/v2/{path}")
    
    # Ambos NÃO devem ser 404
    assert response_v1.status_code != 404, f"V1 path /api/v1/{path} not found"
    assert response_v2.status_code != 404, f"V2 path /api/v2/{path} not found"
    
    # Devem retornar o MESMO status code (401 se não logado, 200 se público)
    assert response_v1.status_code == response_v2.status_code, \
        f"Mismatch status code for {path}: v1={response_v1.status_code}, v2={response_v2.status_code}"

def test_v1_v2_health_parity():
    """Verifica se o conteúdo do health é idêntico em ambas."""
    res_v1 = client.get("/api/v1/health")
    res_v2 = client.get("/api/v2/health")
    
    assert res_v1.status_code == 200
    assert res_v2.status_code == 200
    
    data_v1 = res_v1.json()
    data_v2 = res_v2.json()
    
    # Remove timestamp para comparação
    data_v1.pop("timestamp", None)
    data_v2.pop("timestamp", None)
    
    assert data_v1 == data_v2


def test_v2_alias_equivalent_to_v1():
    """Contract guard: v2 must behave as a thin alias for v1."""
    pairs = [
        ("/api/v1/health", "/api/v2/health"),
        ("/api/v1/chat/stream?q=ping&token=invalid&session_id=s1", "/api/v2/chat/stream?q=ping&token=invalid&session_id=s1"),
        ("/api/v1/code-chat/stream?q=ping&token=invalid", "/api/v2/code-chat/stream?q=ping&token=invalid"),
    ]

    for v1_path, v2_path in pairs:
        res_v1 = client.get(v1_path)
        res_v2 = client.get(v2_path)
        assert res_v1.status_code == res_v2.status_code, f"Status mismatch: {v1_path} vs {v2_path}"
