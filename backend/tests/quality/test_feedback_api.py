import pytest
from fastapi.testclient import TestClient
from unittest.mock import AsyncMock, patch

from backend.main import app  # Ajuste o caminho se necessário

@pytest.fixture
def client():
    return TestClient(app)

@pytest.mark.asyncio
async def test_submit_feedback_success(client):
    # Mock do pipeline factory e memory agent
    with patch("backend.api.v1.endpoints.feedback.get_pipeline_factory") as mock_factory:
        mock_memory = AsyncMock()
        mock_memory.save_feedback.return_value = True
        mock_factory.return_value.get_memory_agent.return_value = mock_memory
        
        response = client.post("/api/v1/feedback", json={
            "request_id": "req-123",
            "user_rating": 5,
            "comment": "Muito bom!"
        })
        
        assert response.status_code == 200
        assert response.json()["status"] == "success"
        mock_memory.save_feedback.assert_called_once_with(
            request_id="req-123",
            rating=5,
            comment="Muito bom!"
        )

@pytest.mark.asyncio
async def test_submit_feedback_invalid_rating(client):
    response = client.post("/api/v1/feedback", json={
        "request_id": "req-123",
        "user_rating": 6  # Inválido (max 5)
    })
    assert response.status_code == 422
