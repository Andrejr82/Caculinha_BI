import asyncio
import base64
import uuid

from fastapi.testclient import TestClient

from backend.main import app
from backend.app.api.dependencies import get_current_active_user
from backend.app.core.utils.session_manager import SessionManager
from backend.infrastructure.adapters.duckdb_vector_adapter import DuckDBVectorAdapter
from backend.services.metrics import MetricsService


class IngestUser:
    def __init__(self, role: str = "analyst"):
        self.id = uuid.uuid4()
        self.username = "ingest-user"
        self.email = "ingest@example.com"
        self.role = role
        self.is_active = True


class StubImageAnalysisService:
    async def analyze_image(self, image_bytes, mime_type, filename, prompt=""):
        return type(
            "ImageAnalysisResult",
            (),
            {
                "summary": "A imagem mostra uma gôndola com ruptura de estoque e etiqueta promocional.",
                "mode": "stub_vision",
                "provider": "test_double",
                "metadata": {
                    "mime_type": mime_type,
                    "detected_format": "png",
                    "size_bytes": len(image_bytes),
                },
            },
        )()


PNG_1X1 = base64.b64decode(
    "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/x8AAwMCAO5X4w0AAAAASUVORK5CYII="
)


def _reset_metrics() -> MetricsService:
    metrics = MetricsService()
    metrics.reset()
    return metrics


def test_ingest_file_indexes_internal_document_for_rag(tmp_path, monkeypatch):
    db_path = tmp_path / "agentbi.db"
    vector_db_path = db_path.with_name("conversation_vectors.duckdb")
    monkeypatch.setattr(
        SessionManager,
        "default_db_path",
        staticmethod(lambda: db_path),
    )

    metrics = _reset_metrics()
    current_user = IngestUser()

    async def _override_user():
        return current_user

    app.dependency_overrides[get_current_active_user] = _override_user
    try:
        with TestClient(app) as client:
            response = client.post(
                "/api/v1/ingest/file",
                data={"session_id": "sess-chat-upload"},
                files={"file": ("manual.txt", b"Politica interna de estoque e margem por loja.", "text/plain")},
            )
            assert response.status_code == 200
            payload = response.json()
            assert payload["success"] is True
            assert payload["chunks_count"] >= 1

        adapter = DuckDBVectorAdapter(db_path=str(vector_db_path))
        results = asyncio.run(
            adapter.search_documents_by_content(
                query="margem por loja",
                tenant_id="default",
                limit=5,
            )
        )

        assert len(results) >= 1
        assert results[0]["metadata"]["filename"] == "manual.txt"
        assert results[0]["metadata"]["session_id"] == "sess-chat-upload"
        assert str(results[0]["metadata"]["uploaded_by"]) == str(current_user.id)
        assert metrics.get_counter("chat_media_upload_total", labels={"media_type": "document", "status": "accepted"}) == 1
    finally:
        app.dependency_overrides.clear()


def test_ingest_file_rejects_unsupported_extension(tmp_path, monkeypatch):
    db_path = tmp_path / "agentbi.db"
    monkeypatch.setattr(
        SessionManager,
        "default_db_path",
        staticmethod(lambda: db_path),
    )

    metrics = _reset_metrics()
    current_user = IngestUser()

    async def _override_user():
        return current_user

    app.dependency_overrides[get_current_active_user] = _override_user
    try:
        with TestClient(app) as client:
            response = client.post(
                "/api/v1/ingest/file",
                files={"file": ("malware.exe", b"fake", "application/octet-stream")},
            )
            assert response.status_code == 415
            assert "não suportado" in response.json()["detail"]
            assert metrics.get_counter("chat_media_upload_total", labels={"media_type": "document", "status": "rejected"}) == 1
    finally:
        app.dependency_overrides.clear()


def test_ingest_file_requires_multimodal_capability(tmp_path, monkeypatch):
    db_path = tmp_path / "agentbi.db"
    monkeypatch.setattr(
        SessionManager,
        "default_db_path",
        staticmethod(lambda: db_path),
    )

    current_user = IngestUser(role="viewer")

    async def _override_user():
        return current_user

    app.dependency_overrides[get_current_active_user] = _override_user
    try:
        with TestClient(app) as client:
            response = client.post(
                "/api/v1/ingest/file",
                files={"file": ("manual.txt", b"conteudo permitido", "text/plain")},
            )
            assert response.status_code == 403
            assert "Anexos" in response.json()["detail"]
    finally:
        app.dependency_overrides.clear()


def test_ingest_file_rejects_binary_payload(tmp_path, monkeypatch):
    db_path = tmp_path / "agentbi.db"
    monkeypatch.setattr(
        SessionManager,
        "default_db_path",
        staticmethod(lambda: db_path),
    )

    _reset_metrics()
    current_user = IngestUser()

    async def _override_user():
        return current_user

    app.dependency_overrides[get_current_active_user] = _override_user
    try:
        with TestClient(app) as client:
            response = client.post(
                "/api/v1/ingest/file",
                files={"file": ("manual.txt", b"abc\x00def", "text/plain")},
            )
            assert response.status_code == 400
            assert "binário" in response.json()["detail"]
    finally:
        app.dependency_overrides.clear()


def test_ingest_file_rejects_oversized_payload(tmp_path, monkeypatch):
    db_path = tmp_path / "agentbi.db"
    monkeypatch.setattr(
        SessionManager,
        "default_db_path",
        staticmethod(lambda: db_path),
    )

    _reset_metrics()
    current_user = IngestUser()

    async def _override_user():
        return current_user

    app.dependency_overrides[get_current_active_user] = _override_user
    try:
        with TestClient(app) as client:
            response = client.post(
                "/api/v1/ingest/file",
                files={"file": ("grande.txt", b"a" * ((2 * 1024 * 1024) + 1), "text/plain")},
            )
            assert response.status_code == 413
            assert "2 MB" in response.json()["detail"]
    finally:
        app.dependency_overrides.clear()


def test_ingest_file_rejects_active_content_payload(tmp_path, monkeypatch):
    db_path = tmp_path / "agentbi.db"
    monkeypatch.setattr(
        SessionManager,
        "default_db_path",
        staticmethod(lambda: db_path),
    )

    _reset_metrics()
    current_user = IngestUser()

    async def _override_user():
        return current_user

    app.dependency_overrides[get_current_active_user] = _override_user
    try:
        with TestClient(app) as client:
            response = client.post(
                "/api/v1/ingest/file",
                files={"file": ("manual.md", b"# teste\n<script>alert('xss')</script>", "text/markdown")},
            )
            assert response.status_code == 400
            assert "Conteúdo ativo" in response.json()["detail"]
    finally:
        app.dependency_overrides.clear()


def test_ingest_image_indexes_analysis_for_rag(tmp_path, monkeypatch):
    db_path = tmp_path / "agentbi.db"
    vector_db_path = db_path.with_name("conversation_vectors.duckdb")
    monkeypatch.setattr(
        SessionManager,
        "default_db_path",
        staticmethod(lambda: db_path),
    )

    metrics = _reset_metrics()
    current_user = IngestUser()

    async def _override_user():
        return current_user

    from backend.app.api.v1.endpoints.ingest import set_ingest_dependencies

    app.dependency_overrides[get_current_active_user] = _override_user
    try:
        with TestClient(app) as client:
            set_ingest_dependencies(
                app.state.ingest_vector_adapter,
                app.state.ingest_vectorization_agent,
                StubImageAnalysisService(),
            )

            response = client.post(
                "/api/v1/ingest/image",
                data={"session_id": "sess-image-1"},
                files={"file": ("ruptura.png", PNG_1X1, "image/png")},
            )
            assert response.status_code == 200
            payload = response.json()
            assert payload["success"] is True
            assert "gôndola" in payload["analysis_summary"]

        adapter = DuckDBVectorAdapter(db_path=str(vector_db_path))
        results = asyncio.run(
            adapter.search_documents_by_content(
                query="ruptura de estoque",
                tenant_id="default",
                limit=5,
            )
        )

        assert len(results) >= 1
        assert results[0]["metadata"]["media_type"] == "image"
        assert results[0]["metadata"]["session_id"] == "sess-image-1"
        assert results[0]["metadata"]["analysis_mode"] == "stub_vision"
        assert metrics.get_counter("chat_media_upload_total", labels={"media_type": "image", "status": "accepted"}) == 1
    finally:
        app.dependency_overrides.clear()


def test_ingest_image_rejects_unsupported_extension(tmp_path, monkeypatch):
    db_path = tmp_path / "agentbi.db"
    monkeypatch.setattr(
        SessionManager,
        "default_db_path",
        staticmethod(lambda: db_path),
    )

    metrics = _reset_metrics()
    current_user = IngestUser()

    async def _override_user():
        return current_user

    app.dependency_overrides[get_current_active_user] = _override_user
    try:
        with TestClient(app) as client:
            response = client.post(
                "/api/v1/ingest/image",
                files={"file": ("animacao.gif", PNG_1X1, "image/gif")},
            )
            assert response.status_code == 415
            assert "não suportado" in response.json()["detail"]
            assert metrics.get_counter("chat_media_upload_total", labels={"media_type": "image", "status": "rejected"}) == 1
    finally:
        app.dependency_overrides.clear()


def test_ingest_image_rejects_mismatched_content_type(tmp_path, monkeypatch):
    db_path = tmp_path / "agentbi.db"
    monkeypatch.setattr(
        SessionManager,
        "default_db_path",
        staticmethod(lambda: db_path),
    )

    _reset_metrics()
    current_user = IngestUser()

    async def _override_user():
        return current_user

    app.dependency_overrides[get_current_active_user] = _override_user
    try:
        with TestClient(app) as client:
            response = client.post(
                "/api/v1/ingest/image",
                files={"file": ("ruptura.png", PNG_1X1, "text/plain")},
            )
            assert response.status_code == 415
            assert "Content-Type incompatível" in response.json()["detail"]
    finally:
        app.dependency_overrides.clear()


def test_ingest_image_rejects_oversized_payload(tmp_path, monkeypatch):
    db_path = tmp_path / "agentbi.db"
    monkeypatch.setattr(
        SessionManager,
        "default_db_path",
        staticmethod(lambda: db_path),
    )

    _reset_metrics()
    current_user = IngestUser()

    async def _override_user():
        return current_user

    app.dependency_overrides[get_current_active_user] = _override_user
    try:
        with TestClient(app) as client:
            response = client.post(
                "/api/v1/ingest/image",
                files={"file": ("grande.png", b"x" * ((5 * 1024 * 1024) + 1), "image/png")},
            )
            assert response.status_code == 413
            assert "5 MB" in response.json()["detail"]
    finally:
        app.dependency_overrides.clear()
