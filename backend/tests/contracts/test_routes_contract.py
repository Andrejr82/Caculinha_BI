"""
Route Contract Tests - Prevent 404 Regressions

These tests verify that all expected routes exist and return appropriate status codes.
They should be run before any deployment to catch API contract breaks.

Usage:
    pytest backend/tests/contracts/test_routes_contract.py -v

Expected behavior:
    - Public routes: 200 or 401 (auth required)
    - Admin routes with admin token: 200
    - Admin routes without admin token: 403
    - Non-existent routes: 404 (should NOT happen for core routes)
"""

import pytest
import jwt
from datetime import datetime, timedelta
from fastapi.testclient import TestClient

from backend.main import app
from backend.app.api.middleware.auth import JWT_SECRET, JWT_ALGORITHM

ADMIN_EMAIL = "user@agentbi.com"

@pytest.fixture(scope="module")
def client():
    return TestClient(app)


def create_token(role: str = "user", username: str = "test_user") -> str:
    """Create a JWT token for testing."""
    return jwt.encode({
        "sub": "12345678-1234-1234-1234-123456789012",
        "user_id": "12345678-1234-1234-1234-123456789012",
        "username": username,
        "role": role,
        "tenant_id": "default",
        "exp": datetime.utcnow() + timedelta(hours=1)
    }, JWT_SECRET, algorithm=JWT_ALGORITHM)


# =============================================================================
# PUBLIC ROUTES (should exist and not return 404)
# =============================================================================

PUBLIC_ROUTES = [
    ("GET", "/"),
    ("GET", "/ping"),
    ("GET", "/health"),
    ("GET", "/docs"),
    ("GET", "/openapi.json"),
]

@pytest.mark.parametrize("method,path", PUBLIC_ROUTES)
def test_public_routes_not_404(client, method, path):
    """Public routes should never return 404."""
    if method == "GET":
        r = client.get(path)
    elif method == "POST":
        r = client.post(path, json={})
    
    assert r.status_code != 404, f"{method} {path} returned 404 - route not registered"


# =============================================================================
# AUTH ROUTES (should exist and return appropriate codes)
# =============================================================================

AUTH_ROUTES = [
    ("POST", "/api/v1/auth/login", {"username": "x", "password": "y"}, [200, 401, 422]),
]

@pytest.mark.parametrize("method,path,body,valid_codes", AUTH_ROUTES)
def test_auth_routes_not_404(client, method, path, body, valid_codes):
    """Auth routes should exist and return expected codes."""
    if method == "POST":
        r = client.post(path, json=body)
    
    assert r.status_code != 404, f"{method} {path} returned 404"
    assert r.status_code in valid_codes, f"{method} {path} returned unexpected {r.status_code}"


# =============================================================================
# PROTECTED ROUTES (require auth, should not 404)
# =============================================================================

PROTECTED_ROUTES = [
    ("GET", "/api/v1/metrics/business-kpis"),
    ("GET", "/api/v1/analytics/data"),
    ("GET", "/api/v1/chat/history"),
]

@pytest.mark.parametrize("method,path", PROTECTED_ROUTES)
def test_protected_routes_require_auth(client, method, path):
    """Protected routes should return 401/403 without auth, not 404."""
    if method == "GET":
        r = client.get(path)
    
    assert r.status_code != 404, f"{method} {path} returned 404 - route not registered"
    assert r.status_code in [401, 403], f"Expected 401/403, got {r.status_code}"


# =============================================================================
# ADMIN ROUTES (require admin role)
# =============================================================================

ADMIN_ROUTES = [
    ("GET", "/api/v1/admin/dashboard/health"),
    ("GET", "/api/v1/admin/dashboard/traffic"),
    ("GET", "/api/v1/admin/dashboard/usage"),
    ("GET", "/api/v1/admin/dashboard/quality"),
    ("GET", "/api/v1/admin/evals"),
]

@pytest.mark.parametrize("method,path", ADMIN_ROUTES)
def test_admin_routes_accessible_to_admin(client, method, path):
    """Admin routes should return 200 for admin users."""
    token = create_token(role="admin", username=ADMIN_EMAIL)
    headers = {"Authorization": f"Bearer {token}"}
    
    if method == "GET":
        r = client.get(path, headers=headers)
    
    assert r.status_code != 404, f"{method} {path} returned 404 - route not registered"
    assert r.status_code == 200, f"Admin should get 200, got {r.status_code}"


@pytest.mark.parametrize("method,path", ADMIN_ROUTES)
def test_admin_routes_blocked_for_non_admin(client, method, path):
    """Admin routes should return 403 for non-admin users."""
    token = create_token(role="user", username="regular@example.com")
    headers = {"Authorization": f"Bearer {token}"}
    
    if method == "GET":
        r = client.get(path, headers=headers)
    
    assert r.status_code != 404, f"{method} {path} returned 404 - route not registered"
    assert r.status_code == 403, f"Non-admin should get 403, got {r.status_code}"


# =============================================================================
# FRONTEND-EXPECTED ROUTES (from routes_diff.md analysis)
# =============================================================================

FRONTEND_EXPECTED_ROUTES = [
    # Dashboard
    ("GET", "/api/v1/dashboard/top-vendidos"),
    ("GET", "/api/v1/dashboard/top-margin"),
    # Admin
    ("GET", "/api/v1/admin/stats"),
    ("GET", "/api/v1/admin/users"),
    # Reports
    ("GET", "/api/v1/reports"),
    # Preferences
    ("GET", "/api/v1/preferences"),
]

@pytest.mark.parametrize("method,path", FRONTEND_EXPECTED_ROUTES)
def test_frontend_expected_routes_not_404(client, method, path):
    """Routes expected by frontend should NOT return 404."""
    token = create_token(role="admin", username=ADMIN_EMAIL)
    headers = {"Authorization": f"Bearer {token}"}
    
    if method == "GET":
        r = client.get(path, headers=headers)
    
    # Allow any code except 404 (route must exist)
    assert r.status_code != 404, f"""
    FRONTEND CONTRACT VIOLATION:
    {method} {path} returned 404
    
    This route is expected by the frontend but is not registered.
    Check backend/api/v1/router.py and ensure the endpoint exists.
    """
