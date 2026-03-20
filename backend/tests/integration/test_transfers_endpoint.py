from __future__ import annotations

import json
from datetime import datetime, timedelta
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from backend.main import app
from backend.app.api.v1.endpoints import transfers as transfers_endpoint

client = TestClient(app)


@pytest.fixture(autouse=True)
def override_current_user():
    """Bypass auth dependency for this module using the endpoint-local dependency ref."""
    mock_user = SimpleNamespace(
        username="testuser",
        id="user123",
        is_active=True,
        role="admin",
    )

    async def _override_user():
        return mock_user

    app.dependency_overrides[transfers_endpoint.get_current_active_user] = _override_user
    try:
        yield mock_user
    finally:
        app.dependency_overrides.pop(transfers_endpoint.get_current_active_user, None)


@pytest.fixture
def mock_tools():
    validar_tool = MagicMock()
    validar_tool.invoke.return_value = {
        "status": "sucesso",
        "mensagem": "Transferência validada e possível.",
    }

    sugerir_tool = MagicMock()
    sugerir_tool.invoke.return_value = [
        {
            "produto_id": 101,
            "une_origem": 1,
            "une_destino": 2,
            "quantidade_sugerida": 5,
            "mensagem": "Sugestão 1",
        },
        {
            "produto_id": 102,
            "une_origem": 3,
            "une_destino": 4,
            "quantidade_sugerida": 10,
            "mensagem": "Sugestão 2",
        },
    ]

    with (
        patch.object(transfers_endpoint, "validar_transferencia_produto", validar_tool),
        patch.object(transfers_endpoint, "sugerir_transferencias_automaticas", sugerir_tool),
    ):
        yield validar_tool, sugerir_tool


@pytest.fixture
def clean_transfer_requests_dir():
    transfer_requests_dir = transfers_endpoint.TRANSFER_REQUESTS_DIR
    transfer_requests_dir.mkdir(parents=True, exist_ok=True)

    for f in transfer_requests_dir.glob("*.json"):
        f.unlink(missing_ok=True)

    yield transfer_requests_dir

    for f in transfer_requests_dir.glob("*.json"):
        f.unlink(missing_ok=True)


def _base_payload() -> dict:
    return {
        "produto_id": 123,
        "une_origem": 10,
        "une_destino": 20,
        "quantidade": 5,
        "solicitante_id": "ignored_by_endpoint",
    }


def test_validate_transfer_success(mock_tools):
    validar_tool, _ = mock_tools
    response = client.post("/api/v1/transfers/validate", json=_base_payload())
    assert response.status_code == 200

    body = response.json()
    assert body["status"] == "sucesso"
    assert body["mensagem"] == "Transferência validada e possível."
    assert "score_prioridade" in body
    assert "nivel_urgencia" in body

    validar_tool.invoke.assert_called_once_with(
        {
            "produto_id": 123,
            "une_origem": 10,
            "une_destino": 20,
            "quantidade": 5,
        }
    )


def test_validate_transfer_invalid_payload(mock_tools):
    payload = _base_payload()
    payload["produto_id"] = "invalid"
    response = client.post("/api/v1/transfers/validate", json=payload)
    assert response.status_code == 422


def test_get_transfer_suggestions_success(mock_tools):
    _, sugerir_tool = mock_tools
    response = client.get("/api/v1/transfers/suggestions")
    assert response.status_code == 200
    assert len(response.json()) == 2
    assert response.json()[0]["produto_id"] == 101

    sugerir_tool.invoke.assert_called_once_with(
        {"segmento": None, "une_origem_excluir": None, "limite": 5}
    )


def test_get_transfer_suggestions_with_params(mock_tools):
    _, sugerir_tool = mock_tools
    response = client.get("/api/v1/transfers/suggestions?segmento=A&limit=1")
    assert response.status_code == 200
    assert len(response.json()) == 2

    sugerir_tool.invoke.assert_called_once_with(
        {"segmento": "A", "une_origem_excluir": None, "limite": 1}
    )


def test_create_transfer_request_success(clean_transfer_requests_dir):
    payload = _base_payload()
    payload.update(
        {
            "produto_id": 1001,
            "une_origem": 100,
            "une_destino": 200,
            "quantidade": 15,
        }
    )
    response = client.post("/api/v1/transfers", json=payload)
    assert response.status_code == 200

    body = response.json()
    assert "message" in body
    assert "transfer_id" in body

    file_path = clean_transfer_requests_dir / f"{body['transfer_id']}.json"
    assert file_path.exists()

    with file_path.open("r", encoding="utf-8") as f:
        saved_data = json.load(f)
    assert saved_data["produto_id"] == 1001
    assert saved_data["solicitante_id"] == "testuser"


def test_get_transfers_report_success(clean_transfer_requests_dir):
    payload = _base_payload()
    payload.update(
        {
            "produto_id": 2001,
            "une_origem": 10,
            "une_destino": 30,
            "quantidade": 25,
        }
    )
    create_response = client.post("/api/v1/transfers", json=payload)
    assert create_response.status_code == 200

    response = client.get("/api/v1/transfers/report")
    assert response.status_code == 200

    body = response.json()
    assert len(body) == 1
    assert body[0]["produto_id"] == 2001


def test_get_transfers_report_with_date_filter(clean_transfer_requests_dir):
    past_date = (datetime.now() - timedelta(days=2)).isoformat()
    past_payload = {
        "produto_id": 3001,
        "une_origem": 1,
        "une_destino": 2,
        "quantidade": 10,
        "solicitante_id": "testuser",
        "timestamp": past_date,
    }
    past_file_path = clean_transfer_requests_dir / "transfer_past.json"
    with past_file_path.open("w", encoding="utf-8") as f:
        json.dump(past_payload, f)

    current_payload = _base_payload()
    current_payload.update({"produto_id": 3002, "une_origem": 3, "une_destino": 4, "quantidade": 15})
    create_response = client.post("/api/v1/transfers", json=current_payload)
    assert create_response.status_code == 200

    end_date = (datetime.now() - timedelta(days=1)).isoformat()
    response = client.get(f"/api/v1/transfers/report?end_date={end_date}")
    assert response.status_code == 200

    body = response.json()
    assert len(body) == 1
    assert body[0]["produto_id"] == 3001
