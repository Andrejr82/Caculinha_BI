"""
Testes unitários para o endpoint de Transfers
"""
import pytest
from fastapi.testclient import TestClient


def test_get_transfers_success(client: TestClient, test_user_token: str):
    """
    Testa se o endpoint de transferências retorna dados válidos
    """
    response = client.get(
        "/api/v1/transfers/list",
        headers={"Authorization": f"Bearer {test_user_token}"}
    )
    
    assert response.status_code == 200
    data = response.json()
    
    # Verificar que retorna uma lista
    assert isinstance(data, list)
    
    # Se houver transferências, verificar estrutura
    if len(data) > 0:
        transfer = data[0]
        # Verificar campos esperados do Parquet
        expected_fields = ["PRODUTO", "NOME", "UNE", "ESTOQUE_UNE", "VENDA_30DD"]
        for field in expected_fields:
            assert field in transfer


def test_get_transfers_with_limit(client: TestClient, test_user_token: str):
    """
    Testa se o parâmetro limit funciona corretamente
    """
    limit = 10
    response = client.get(
        f"/api/v1/transfers/list?limit={limit}",
        headers={"Authorization": f"Bearer {test_user_token}"}
    )
    
    assert response.status_code == 200
    data = response.json()
    
    # Verificar que não retorna mais que o limite
    assert len(data) <= limit


def test_get_transfers_unauthorized(client: TestClient):
    """
    Testa se o endpoint rejeita requisições sem autenticação
    """
    response = client.get("/api/v1/transfers/list")
    assert response.status_code == 401


def test_get_transfers_data_quality(client: TestClient, test_user_token: str):
    """
    Testa a qualidade dos dados retornados
    """
    response = client.get(
        "/api/v1/transfers/list?limit=5",
        headers={"Authorization": f"Bearer {test_user_token}"}
    )
    
    assert response.status_code == 200
    data = response.json()
    
    for transfer in data:
        # Verificar que VENDA_30DD é maior que 0 (filtro do endpoint)
        assert transfer["VENDA_30DD"] > 0
        
        # Verificar tipos de dados
        assert isinstance(transfer["PRODUTO"], str)
        assert isinstance(transfer["NOME"], str)
        assert isinstance(transfer["UNE"], str)


def test_get_transfers_with_admin(client: TestClient, test_admin_token: str):
    """
    Testa se admin tem acesso às transferências
    """
    response = client.get(
        "/api/v1/transfers/list",
        headers={"Authorization": f"Bearer {test_admin_token}"}
    )
    
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
