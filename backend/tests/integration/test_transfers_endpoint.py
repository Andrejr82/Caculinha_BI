# backend/tests/integration/test_transfers_endpoint.py

import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, AsyncMock, MagicMock
import json
import os
from pathlib import Path
from datetime import datetime, timedelta

from main import app
from app.config.settings import settings

client = TestClient(app)

@pytest.fixture(autouse=True)
def mock_auth_and_tools():
    with patch('backend.app.api.dependencies.get_current_active_user', new_callable=AsyncMock) as mock_get_current_active_user, \
         patch('backend.app.core.tools.une_tools.validar_transferencia_produto') as mock_validar_transferencia_produto, \
         patch('backend.app.core.tools.une_tools.sugerir_transferencias_automaticas') as mock_sugerir_transferencias_automaticas:
        
        # Mock get_current_active_user to return a valid user
        mock_user = MagicMock()
        mock_user.username = "testuser"
        mock_user.id = "user123"
        mock_user.is_active = True
        mock_user.role = "admin"
        mock_get_current_active_user.return_value = mock_user

        # Mock une_tools functions
        mock_validar_transferencia_produto.return_value = {"status": "sucesso", "mensagem": "Transferência validada e possível."}
        mock_sugerir_transferencias_automaticas.return_value = [
            {"produto_id": 101, "une_origem": 1, "une_destino": 2, "quantidade_sugerida": 5, "mensagem": "Sugestão 1"},
            {"produto_id": 102, "une_origem": 3, "une_destino": 4, "quantidade_sugerida": 10, "mensagem": "Sugestão 2"}
        ]
        yield

@pytest.fixture
def clean_transfer_requests_dir():
    # Ensure a clean directory for transfer requests before and after tests
    test_dir = Path(settings.APP_NAME) / "data" / "transferencias" # This path is not correct. It should be just 'data/transferencias'
    
    # Correct path setup (assuming current working directory is project root)
    current_dir = Path(__file__).parent.parent.parent.parent.parent
    transfer_requests_dir = current_dir / "data" / "transferencias"

    os.makedirs(transfer_requests_dir, exist_ok=True)
    for f in os.listdir(transfer_requests_dir):
        if f.startswith("transfer_") and f.endswith(".json"):
            os.remove(transfer_requests_dir / f)
    yield
    for f in os.listdir(transfer_requests_dir):
        if f.startswith("transfer_") and f.endswith(".json"):
            os.remove(transfer_requests_dir / f)


# Test cases for /transfers/validate
def test_validate_transfer_success(mock_auth_and_tools):
    payload = {
        "produto_id": 123,
        "une_origem": 10,
        "une_destino": 20,
        "quantidade": 5
    }
    response = client.post("/api/v1/transfers/validate", json=payload, headers={"Authorization": "Bearer mock_token"})
    assert response.status_code == 200
    assert response.json()["status"] == "sucesso"
    assert response.json()["mensagem"] == "Transferência validada e possível."
    assert backend.app.core.tools.une_tools.validar_transferencia_produto.called_once_with(
        produto_id=123, une_origem=10, une_destino=20, quantidade=5
    )

def test_validate_transfer_invalid_payload(mock_auth_and_tools):
    payload = {
        "produto_id": "invalid", # Invalid type
        "une_origem": 10,
        "une_destino": 20,
        "quantidade": 5
    }
    response = client.post("/api/v1/transfers/validate", json=payload, headers={"Authorization": "Bearer mock_token"})
    assert response.status_code == 422 # Unprocessable Entity (Pydantic validation error)

# Test cases for /transfers/suggestions
def test_get_transfer_suggestions_success(mock_auth_and_tools):
    response = client.get("/api/v1/transfers/suggestions", headers={"Authorization": "Bearer mock_token"})
    assert response.status_code == 200
    assert len(response.json()) == 2
    assert response.json()[0]["produto_id"] == 101
    assert backend.app.core.tools.une_tools.sugerir_transferencias_automaticas.called_once()

def test_get_transfer_suggestions_with_params(mock_auth_and_tools):
    response = client.get("/api/v1/transfers/suggestions?segmento=A&limit=1", headers={"Authorization": "Bearer mock_token"})
    assert response.status_code == 200
    assert len(response.json()) == 2 # Mock returns 2, so it will return 2
    assert backend.app.core.tools.une_tools.sugerir_transferencias_automaticas.called_once_with(
        segmento="A", une_origem_excluir=None, limite=1
    )

# Test cases for /transfers
def test_create_transfer_request_success(mock_auth_and_tools, clean_transfer_requests_dir):
    payload = {
        "produto_id": 1001,
        "une_origem": 100,
        "une_destino": 200,
        "quantidade": 15
    }
    response = client.post("/api/v1/transfers", json=payload, headers={"Authorization": "Bearer mock_token"})
    assert response.status_code == 200
    assert "message" in response.json()
    assert "transfer_id" in response.json()

    # Verify file creation
    transfer_id = response.json()["transfer_id"]
    transfer_requests_dir = Path("data/transferencias")
    file_path = transfer_requests_dir / f"{transfer_id}.json"
    assert file_path.exists()
    
    with open(file_path, "r", encoding="utf-8") as f:
        saved_data = json.load(f)
        assert saved_data["produto_id"] == 1001
        assert saved_data["solicitante_id"] == "testuser"

# Test cases for /transfers/report
def test_get_transfers_report_success(mock_auth_and_tools, clean_transfer_requests_dir):
    # Create a dummy transfer request first
    create_payload = {
        "produto_id": 2001,
        "une_origem": 10,
        "une_destino": 30,
        "quantidade": 25
    }
    client.post("/api/v1/transfers", json=create_payload, headers={"Authorization": "Bearer mock_token"})
    
    response = client.get("/api/v1/transfers/report", headers={"Authorization": "Bearer mock_token"})
    assert response.status_code == 200
    assert len(response.json()) == 1
    assert response.json()[0]["produto_id"] == 2001

def test_get_transfers_report_with_date_filter(mock_auth_and_tools, clean_transfer_requests_dir):
    # Create two dummy transfer requests, one in the past
    past_date = (datetime.now() - timedelta(days=2)).isoformat()
    future_date = (datetime.now() + timedelta(days=2)).isoformat()

    # Past transfer
    past_payload = {
        "produto_id": 3001, "une_origem": 1, "une_destino": 2, "quantidade": 10,
        "solicitante_id": "testuser", "timestamp": past_date
    }
    transfer_requests_dir = Path("data/transferencias")
    past_file_path = transfer_requests_dir / f"transfer_past.json"
    with open(past_file_path, "w", encoding="utf-8") as f:
        json.dump(past_payload, f)

    # Current transfer
    current_payload = {
        "produto_id": 3002, "une_origem": 3, "une_destino": 4, "quantidade": 15
    }
    client.post("/api/v1/transfers", json=current_payload, headers={"Authorization": "Bearer mock_token"})

    # Test with end_date filter to exclude the current transfer
    response = client.get(f"/api/v1/transfers/report?end_date={(datetime.now() - timedelta(days=1)).isoformat()}", headers={"Authorization": "Bearer mock_token"})
    assert response.status_code == 200
    assert len(response.json()) == 1
    assert response.json()[0]["produto_id"] == 3001

    # Clean up manually created file
    if os.path.exists(past_file_path):
        os.remove(past_file_path)
