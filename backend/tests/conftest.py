"""Test configuration"""

import pytest
import sys
import os
from httpx import AsyncClient

# Add project root to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from main import app


@pytest.fixture
async def client():
    """Async test client"""
    async with AsyncClient(app=app, base_url="http://test") as client:
        yield client


@pytest.fixture
def admin_token():
    """Admin JWT token for testing"""
    from app.config.security import create_access_token
    return create_access_token({
        "sub": "admin-id",
        "username": "admin",
        "role": "admin"
    })


@pytest.fixture
def user_token():
    """User JWT token for testing"""
    from app.config.security import create_access_token
    return create_access_token({
        "sub": "user-id",
        "username": "user",
        "role": "user"
    })
