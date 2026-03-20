
import os
import sys
from pathlib import Path
import uuid

import pytest
from fastapi.testclient import TestClient

# Testes não devem depender de provedor LLM externo.
os.environ.setdefault("LLM_PROVIDER", "mock")
os.environ.setdefault("LLM_FALLBACK_PROVIDERS", "mock")
os.environ.setdefault("GROQ_API_KEY", "")
os.environ.setdefault("GEMINI_API_KEY", "")

# Injeta o diretório 'backend' no sys.path para permitir "import app..."
# Isso é necessário porque o código legada e a maioria dos módulos assumem que 'app' é importável diretamente.
BACKEND_ROOT = Path(__file__).parent.parent
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

# Injeta a raiz do projeto também, se necessário
PROJECT_ROOT = BACKEND_ROOT.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.append(str(PROJECT_ROOT))

from backend.main import app
from backend.app.config.security import create_access_token


@pytest.fixture(scope="session")
def client():
    return TestClient(app)


def _build_token(role: str) -> str:
    user_id = str(uuid.uuid4())
    payload = {
        "sub": user_id,
        "user_id": user_id,
        "username": f"{role}_user",
        "email": f"{role}@example.com",
        "role": role,
        "allowed_segments": ["*"],
    }
    return create_access_token(payload)


@pytest.fixture
def test_user_token() -> str:
    return _build_token("user")


@pytest.fixture
def test_admin_token() -> str:
    return _build_token("admin")
