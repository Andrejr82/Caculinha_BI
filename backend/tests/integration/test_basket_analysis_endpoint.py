from __future__ import annotations

import uuid

from fastapi.testclient import TestClient

from backend.main import app
from backend.app.api.dependencies import get_current_active_user
from backend.app.api.v1.endpoints.basket_analysis import get_basket_analysis_service
from backend.app.infrastructure.database.models import User
from backend.app.services.basket_analysis_service import BasketAnalysisService

from backend.tests.unit.test_basket_analysis_service import _build_strong_transaction_dataset


class StaticBasketAnalysisService(BasketAnalysisService):
    def __init__(self, frame):
        self._frame = frame

    def _load_source_frame(self, user=None):  # type: ignore[override]
        return self._frame.copy(), list(self._frame.columns)


def _override_user() -> User:
    return User(
        id=uuid.uuid4(),
        username="analyst",
        email="analyst@example.com",
        hashed_password="x",
        role="analyst",
        allowed_segments='["*"]',
        is_active=True,
    )


def test_basket_analysis_endpoint_returns_structured_payload() -> None:
    app.dependency_overrides[get_current_active_user] = _override_user
    app.dependency_overrides[get_basket_analysis_service] = lambda: StaticBasketAnalysisService(
        _build_strong_transaction_dataset()
    )
    try:
        with TestClient(app) as client:
            response = client.post(
                "/api/v1/analytics/basket-analysis",
                json={"min_support": 0.2, "min_confidence": 0.6, "max_rules": 5},
            )
            assert response.status_code == 200
            payload = response.json()
            assert payload["status"] == "success"
            assert payload["analysis_mode"] == "real_transactional"
            assert payload["transactions_analyzed"] == 120
            assert "top_rules" in payload
    finally:
        app.dependency_overrides.clear()


def test_basket_analysis_endpoint_has_v2_alias() -> None:
    app.dependency_overrides[get_current_active_user] = _override_user
    app.dependency_overrides[get_basket_analysis_service] = lambda: StaticBasketAnalysisService(
        _build_strong_transaction_dataset()
    )
    try:
        with TestClient(app) as client:
            response = client.post("/api/v2/analytics/basket-analysis", json={})
            assert response.status_code == 200
            assert response.json()["analysis_mode"] == "real_transactional"
    finally:
        app.dependency_overrides.clear()
